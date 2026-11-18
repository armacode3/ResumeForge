"""Explicit selection/count plans never imply ranking, supported wording or page feasibility."""

import json
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from resumeforge.jobs import JobDocument, JobRequirements
from resumeforge.planning import (
    PlanningError,
    PlanSelection,
    ResumePlan,
    parse_selection,
    plan_resume,
)
from resumeforge.profile import UserProfile


@pytest.fixture
def planning_profile() -> UserProfile:
    return UserProfile.model_validate(
        {
            "schema_version": 1,
            "person": {"name": "Private fictional name", "email": "private@example.com"},
            "education": [
                {"id": "edu_demo", "title": "Degree", "completion_status": "in_progress"}
            ],
            "experiences": [
                {"id": "exp_demo", "title": "Intern", "completion_status": "completed"}
            ],
            "projects": [
                {"id": "proj_demo", "title": "Prototype", "completion_status": "in_progress"}
            ],
            "skills": {"languages": ["Python"]},
            "coursework": ["Databases"],
            "accomplishments": [
                {
                    "id": "acc_exp",
                    "entry_id": "exp_demo",
                    "statement": "Added Python tests under mentor review.",
                    "verified": True,
                    "completion_status": "completed",
                    "technologies": ["Python"],
                },
                {
                    "id": "acc_proj",
                    "entry_id": "proj_demo",
                    "statement": "Built a Python prototype, not a production service.",
                    "verified": True,
                    "completion_status": "completed",
                    "technologies": ["Python"],
                },
            ],
        }
    )


@pytest.fixture
def planning_requirements(empty_job_payload: dict[str, Any]) -> JobRequirements:
    empty_job_payload["required_qualifications"] = [
        {
            "id": "job_python",
            "text": "Python or Java; either is sufficient.",
            "source_quote": "Python or Java; either is sufficient.",
        }
    ]
    empty_job_payload["preferred_qualifications"] = [
        {
            "id": "job_sql",
            "text": "SQL preferred.",
            "source_quote": "SQL preferred.",
        }
    ]
    return JobRequirements.model_validate(empty_job_payload)


@pytest.fixture
def planning_job() -> JobDocument:
    return JobDocument("Python or Java; either is sufficient.\nSQL preferred.")


@pytest.fixture
def selection_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "entries": [
            {"entry_id": "proj_demo", "accomplishment_ids": ["acc_proj"]},
            {"entry_id": "exp_demo", "accomplishment_ids": ["acc_exp"]},
        ],
        "max_total_bullets": 4,
    }


def make_plan(
    profile: UserProfile, job: JobDocument, requirements: JobRequirements, data: dict[str, Any]
) -> ResumePlan:
    return plan_resume(
        profile,
        job,
        requirements,
        PlanSelection.model_validate(data),
        requirements_reviewed=True,
        selection_reviewed=True,
    )


def test_plan_uses_explicit_ids_and_exact_statements_without_network_or_mutation(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
) -> None:
    before = planning_profile.model_dump_json()
    with patch("socket.socket", side_effect=AssertionError("Offline")):
        plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    assert plan.planning_version == "reviewed-selection-plan-v1"
    assert plan.matching_version == "evidence-matching-v1"
    assert plan.signals_version == "evidence-signals-v1"
    assert plan.status == "needs_review"
    assert plan.constraint_status == "within_count_constraints"
    assert plan.requirements_reviewed and plan.selection_reviewed
    assert all(
        len(value) == 64
        for value in (
            plan.profile_model_sha256,
            plan.job_source_sha256,
            plan.requirements_model_sha256,
            plan.selection_model_sha256,
        )
    )
    assert [section.section for section in plan.sections] == ["experiences", "projects"]
    experience = plan.sections[0].entries[0]
    project = plan.sections[1].entries[0]
    assert experience.selection_reason == "user_selected" and not experience.required
    assert experience.bullet_slots[0].statement == planning_profile.accomplishments[0].statement
    assert project.completion_status == "in_progress"
    assert project.bullet_slots[0].caveats == ("parent_entry_in_progress",)
    assert project.bullet_slots[0].job_item_ids == ("job_python",)
    assert (
        plan.job_items[0].text
        == plan.job_items[0].source_quote
        == "Python or Java; either is sufficient."
    )
    assert plan.job_items[0].selected_accomplishment_ids == ("acc_exp", "acc_proj")
    assert plan.job_items[1].section == "preferred_qualifications"
    assert plan.job_items[1].text == "SQL preferred."
    assert plan.job_items[1].selected_accomplishment_ids == ()
    assert plan.budget.project_count == 1 and plan.budget.bullet_slot_count == 2
    assert plan.findings == ()
    assert "private@example.com" not in json.dumps(asdict(plan))
    assert "Private fictional name" not in json.dumps(asdict(plan))
    assert planning_profile.model_dump_json() == before
    assert plan == make_plan(planning_profile, planning_job, planning_requirements, selection_data)


def test_required_entries_and_sections_remain_visible_without_guessing_evidence(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
) -> None:
    planning_profile.resume_preferences.required_entry_ids = ["edu_demo", "exp_demo"]
    planning_profile.resume_preferences.required_sections = [
        "education",
        "experiences",
        "projects",
        "skills",
    ]
    planning_profile.resume_preferences.min_bullets_per_entry = 1
    plan = make_plan(
        planning_profile, planning_job, planning_requirements, {"schema_version": 1, "entries": []}
    )
    assert [section.section for section in plan.sections] == [
        "education",
        "experiences",
        "projects",
        "skills",
    ]
    assert all(section.required for section in plan.sections)
    assert [section.entries[0].entry_id for section in plan.sections[:2]] == [
        "edu_demo",
        "exp_demo",
    ]
    assert all(
        section.entries[0].selection_reason == "required_by_preferences"
        for section in plan.sections[:2]
    )
    assert all(section.entries[0].required for section in plan.sections[:2])
    assert plan.sections[2].entries == ()
    codes = [finding.code for finding in plan.findings]
    assert codes.count("required_entry_added") == 2
    assert codes.count("entry_bullet_minimum_not_met") == 2
    assert "required_section_needs_entry_selection" in codes
    assert "section_requires_separate_evidence_review" in codes
    assert plan.constraint_status == "conflicts"
    assert plan.budget.bullet_slot_count == 0


@pytest.mark.parametrize(
    ("preference", "value", "code", "actual"),
    [
        ("min_bullets_per_entry", 2, "entry_bullet_minimum_not_met", 1),
        ("max_bullets_per_entry", 0, "entry_bullet_maximum_exceeded", 1),
        ("max_projects", 0, "project_maximum_exceeded", 1),
    ],
)
def test_count_conflicts_never_trim_selections_or_fabricate_slots(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
    preference: str,
    value: int,
    code: str,
    actual: int,
) -> None:
    setattr(planning_profile.resume_preferences, preference, value)
    plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    assert plan.constraint_status == "conflicts"
    conflicts = [finding for finding in plan.findings if finding.code == code]
    assert conflicts and all(
        finding.actual == actual and finding.bound == value for finding in conflicts
    )
    assert plan.budget.bullet_slot_count == 2
    assert plan.budget.project_count == 1


def test_project_minimum_uses_selected_entries_not_available_profile_projects(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
) -> None:
    planning_profile.resume_preferences.min_projects = 1
    selection_data["entries"] = selection_data["entries"][1:]
    plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    finding = next(
        finding for finding in plan.findings if finding.code == "project_minimum_not_met"
    )
    assert finding.actual == 0 and finding.bound == 1
    assert plan.budget.project_count == 0


def test_total_budget_conflict_retains_required_content_and_all_selected_slots(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
) -> None:
    planning_profile.resume_preferences.required_entry_ids = ["proj_demo"]
    selection_data["max_total_bullets"] = 1
    plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    assert plan.sections[1].entries[0].required
    assert plan.budget.bullet_slot_count == 2
    finding = next(f for f in plan.findings if f.code == "total_bullet_budget_exceeded")
    assert finding.actual == 2 and finding.bound == 1
    assert plan.constraint_status == "conflicts"


@pytest.mark.parametrize("status", ["unknown", "planned", "on_hold", "cancelled"])
def test_metadata_only_required_entry_keeps_status_and_zero_bullet_bounds(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    status: str,
) -> None:
    data = planning_profile.model_dump()
    data["education"][0]["completion_status"] = status
    data["resume_preferences"] = {
        "required_entry_ids": ["edu_demo"],
        "min_bullets_per_entry": 0,
        "max_bullets_per_entry": 0,
    }
    plan = make_plan(
        UserProfile.model_validate(data),
        planning_job,
        planning_requirements,
        {"schema_version": 1, "entries": [], "max_total_bullets": 0},
    )
    entry = plan.sections[0].entries[0]
    assert entry.completion_status == status and entry.bullet_slots == ()
    assert plan.constraint_status == "within_count_constraints"
    assert "entry_status_requires_review" in [f.code for f in plan.findings]
    assert "metadata_only_entry" in [f.code for f in plan.findings]
    assert plan.status == "needs_review"


@pytest.mark.parametrize(
    "blocker",
    ["excluded", "unverified", "unfinished", "unknown", "parent_unknown", "parent_cancelled"],
)
def test_blocked_evidence_never_becomes_a_slot_or_leaks_claim_text(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
    blocker: str,
) -> None:
    planning_profile.accomplishments[0].statement = "fictional-private-blocked-statement"
    planning_profile.accomplishments[0].metrics = ["fictional-private-blocked-metric"]
    if blocker == "excluded":
        planning_profile.resume_preferences.excluded_entry_ids = ["exp_demo"]
    elif blocker == "unverified":
        planning_profile.accomplishments[0].verified = False
    elif blocker == "unfinished":
        planning_profile.accomplishments[0].completion_status = "in_progress"
    elif blocker == "unknown":
        planning_profile.accomplishments[0].completion_status = "unknown"
    elif blocker == "parent_unknown":
        planning_profile.experiences[0].completion_status = "unknown"
    else:
        planning_profile.experiences[0].completion_status = "cancelled"
    plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    assert plan.constraint_status == "conflicts"
    assert plan.budget.bullet_slot_count == 1
    assert "fictional-private-blocked" not in json.dumps(asdict(plan))
    codes = [f.code for f in plan.findings]
    assert (
        "excluded_entry_selected" if blocker == "excluded" else "selected_evidence_ineligible"
    ) in codes
    if blocker == "excluded":
        assert [section.section for section in plan.sections] == ["projects"]


def test_eligible_unmatched_selection_is_retained_for_review_not_called_missing_experience(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
) -> None:
    planning_profile.accomplishments[0].technologies = []
    plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    slot = plan.sections[0].entries[0].bullet_slots[0]
    assert slot.accomplishment_id == "acc_exp" and slot.job_item_ids == ()
    assert "selected_evidence_without_lexical_link" in [f.code for f in plan.findings]
    assert plan.constraint_status == "within_count_constraints"


@pytest.mark.parametrize("section", ["skills", "coursework"])
@pytest.mark.parametrize("has_content", [True, False])
def test_unscoped_sections_are_review_placeholders_not_inferred_accomplishments(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    section: str,
    has_content: bool,
) -> None:
    if not has_content:
        planning_profile.skills.languages = []
        planning_profile.coursework = []
    plan = make_plan(
        planning_profile,
        planning_job,
        planning_requirements,
        {"schema_version": 1, "entries": [], "include_sections": [section]},
    )
    assert len(plan.sections) == 1 and plan.sections[0].section == section
    assert plan.sections[0].entries == ()
    assert plan.budget.bullet_slot_count == 0
    assert "section_requires_separate_evidence_review" in [f.code for f in plan.findings]
    assert (plan.constraint_status == "conflicts") is (not has_content)


@pytest.mark.parametrize("mode", ["unknown_entry", "unknown_evidence", "wrong_parent"])
def test_broken_selection_references_fail_safely_without_partial_plans(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
    mode: str,
) -> None:
    if mode == "unknown_entry":
        selection_data["entries"][0]["entry_id"] = "proj_private_unknown"
    else:
        selection_data["entries"][0]["accomplishment_ids"] = [
            "acc_private_unknown" if mode == "unknown_evidence" else "acc_exp"
        ]
    with pytest.raises(PlanningError) as error:
        make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    assert "private_unknown" not in str(error.value)


@pytest.mark.parametrize("value", [False, None, 1, "true"])
@pytest.mark.parametrize("gate", ["requirements_reviewed", "selection_reviewed"])
def test_both_review_gates_are_explicit_before_any_matching(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
    value: Any,
    gate: str,
) -> None:
    kwargs = {"requirements_reviewed": True, "selection_reviewed": True, gate: value}
    with (
        patch(
            "resumeforge.planning.engine.match_evidence", side_effect=AssertionError("No matching")
        ),
        pytest.raises(PlanningError, match="Review"),
    ):
        plan_resume(
            planning_profile,
            planning_job,
            planning_requirements,
            PlanSelection.model_validate(selection_data),
            **kwargs,
        )


def test_default_review_is_not_granted(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
) -> None:
    with pytest.raises(PlanningError, match="Review"):
        plan_resume(
            planning_profile,
            planning_job,
            planning_requirements,
            parse_selection('{"schema_version":1,"entries":[]}'),
        )


@pytest.mark.parametrize("mode", ["profile", "selection", "requirements", "source", "budget"])
def test_planning_revalidates_models_quotes_and_comparison_budget(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
    mode: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = PlanSelection.model_validate(selection_data)
    if mode == "profile":
        planning_profile.accomplishments[0].entry_id = "exp_private_unknown"
    elif mode == "selection":
        selection.entries[0].accomplishment_ids = [123]  # type: ignore[list-item]
    elif mode == "requirements":
        planning_requirements = planning_requirements.model_copy(
            update={"required_qualifications": "private-invalid"}
        )
    elif mode == "source":
        planning_job = JobDocument("Different source")
    else:
        monkeypatch.setattr("resumeforge.matching.engine.MAX_MATCH_PAIRS", 0)
    with pytest.raises(PlanningError) as error:
        plan_resume(
            planning_profile,
            planning_job,
            planning_requirements,
            selection,
            requirements_reviewed=True,
            selection_reviewed=True,
        )
    assert "private" not in str(error.value)


def test_plan_is_immutable_and_cannot_be_changed_by_later_input_edits(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
) -> None:
    plan = make_plan(planning_profile, planning_job, planning_requirements, selection_data)
    statement = plan.sections[0].entries[0].bullet_slots[0].statement
    planning_profile.accomplishments[0].statement = "Changed later"
    assert plan.sections[0].entries[0].bullet_slots[0].statement == statement
    with pytest.raises(FrozenInstanceError):
        plan.status = "needs_review"  # type: ignore[misc]


def test_selection_json_bom_and_round_trip(selection_data: dict[str, Any]) -> None:
    selection = parse_selection("\ufeff" + json.dumps(selection_data))
    assert parse_selection(selection.model_dump_json()) == selection


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"schema_version": True, "entries": []},
        {"schema_version": 2, "entries": []},
        {"schema_version": 1, "entries": None},
        {"schema_version": 1, "entries": [], "private": "secret"},
        {
            "schema_version": 1,
            "entries": [{"entry_id": "exp_demo", "accomplishment_ids": ["acc_exp", "acc_exp"]}],
        },
        {"schema_version": 1, "entries": [{"entry_id": "exp_demo", "accomplishment_ids": []}] * 2},
        {"schema_version": 1, "entries": [], "include_sections": ["projects"]},
        {"schema_version": 1, "entries": [], "include_sections": ["skills", "skills"]},
        {"schema_version": 1, "entries": [], "max_total_bullets": True},
        {"schema_version": 1, "entries": [], "max_total_bullets": -1},
        {"schema_version": 1, "entries": [], "max_total_bullets": 21},
    ],
)
def test_invalid_selection_schema_is_safe(payload: dict[str, Any]) -> None:
    with pytest.raises(PlanningError, match="selection fields") as error:
        parse_selection(json.dumps(payload))
    assert "secret" not in str(error.value)


@pytest.mark.parametrize(
    "text",
    [
        "not JSON: fictional-private-value",
        '{"entries":[],"entries":[]}',
        '{"schema_version":1,"entries":[],"max_total_bullets":NaN}',
        "[" * 40 + "0" + "]" * 40,
        "[" * 2000 + "0" + "]" * 2000,
        '{"schema_version":' + "1" * 5000 + "}",
        "\ud800",
        "x" * 1_048_577,
    ],
)
def test_malformed_oversized_deep_or_nonstandard_selection_json_is_safe(text: str) -> None:
    with pytest.raises(PlanningError) as error:
        parse_selection(text)
    assert "fictional-private-value" not in str(error.value)


def test_selection_loader_is_bounded_and_local(
    tmp_path: Path, selection_data: dict[str, Any]
) -> None:
    from resumeforge.inputs import InputError
    from resumeforge.planning import load_selection

    path = tmp_path / "selection.json"
    with pytest.raises(InputError):
        load_selection(path)
    path.write_text(json.dumps(selection_data))
    assert load_selection(path) == PlanSelection.model_validate(selection_data)


def test_selection_order_and_exact_budget_boundaries_do_not_depend_on_metrics_or_keywords(
    planning_profile: UserProfile,
    planning_job: JobDocument,
    planning_requirements: JobRequirements,
    selection_data: dict[str, Any],
) -> None:
    data = planning_profile.model_dump()
    data["experiences"].append({**data["experiences"][0], "id": "exp_aaa"})
    data["accomplishments"].extend(
        [
            {**data["accomplishments"][0], "id": "acc_aaa", "entry_id": "exp_aaa"},
            {**data["accomplishments"][0], "id": "acc_more"},
        ]
    )
    data["resume_preferences"] = {
        "min_projects": 1,
        "max_projects": 1,
        "min_bullets_per_entry": 1,
        "max_bullets_per_entry": 2,
    }
    selection_data["entries"][1]["accomplishment_ids"] = ["acc_more", "acc_exp"]
    selection_data["entries"].append({"entry_id": "exp_aaa", "accomplishment_ids": ["acc_aaa"]})
    profile = UserProfile.model_validate(data)
    plan = make_plan(profile, planning_job, planning_requirements, selection_data)
    assert plan.constraint_status == "within_count_constraints"
    assert plan.budget.bullet_slot_count == plan.budget.max_total_bullets == 4
    assert [entry.entry_id for entry in plan.sections[0].entries] == ["exp_demo", "exp_aaa"]
    assert [slot.accomplishment_id for slot in plan.sections[0].entries[0].bullet_slots] == [
        "acc_more",
        "acc_exp",
    ]
    profile.accomplishments[0].metrics = ["Python"] * 20
    profile.accomplishments[0].technologies = ["Python"] * 20
    updated = make_plan(profile, planning_job, planning_requirements, selection_data)
    assert updated.sections == plan.sections
    assert updated.budget == plan.budget


def test_plan_preserves_every_job_category_and_does_not_promote_negation(
    planning_profile: UserProfile, empty_job_payload: dict[str, Any], selection_data: dict[str, Any]
) -> None:
    for section in JobRequirements.ITEM_FIELDS:
        empty_job_payload[section] = [
            {
                "id": f"job_{section}",
                "text": "Python is not required.",
                "source_quote": "Python is not required.",
            }
        ]
    requirements = JobRequirements.model_validate(empty_job_payload)
    plan = make_plan(
        planning_profile, JobDocument("Python is not required."), requirements, selection_data
    )
    assert [item.section for item in plan.job_items] == list(JobRequirements.ITEM_FIELDS)
    for item in plan.job_items:
        assert item.text == item.source_quote == "Python is not required."
        assert item.selected_accomplishment_ids == ("acc_exp", "acc_proj")
        assert "satisfied" not in asdict(item)


def test_empty_selection_and_legacy_unknown_states_are_not_automatic_fact_approval(
    planning_job: JobDocument, planning_requirements: JobRequirements
) -> None:
    profile = UserProfile.model_validate(
        {
            "schema_version": 1,
            "person": {"name": "Example"},
            "education": [{"id": "edu_demo", "title": "Provisional degree"}],
        }
    )
    plan = make_plan(
        profile, planning_job, planning_requirements, {"schema_version": 1, "entries": []}
    )
    assert plan.sections == () and plan.budget.bullet_slot_count == 0
    assert plan.status == "needs_review"
    plan = make_plan(
        profile,
        planning_job,
        planning_requirements,
        {
            "schema_version": 1,
            "entries": [{"entry_id": "edu_demo", "accomplishment_ids": []}],
        },
    )
    assert plan.sections[0].entries[0].completion_status == "unknown"
    assert "entry_status_requires_review" in [finding.code for finding in plan.findings]
