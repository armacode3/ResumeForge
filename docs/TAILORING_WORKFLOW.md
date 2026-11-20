# Adopted tailoring workflow boundaries

The user approved selectively adopting an evidence-first resume-tailoring prompt. This is a
product workflow policy, **not one giant model prompt**, an installed assistant skill, or a claim
that all stages below are implemented. Application code owns source boundaries, review gates,
selection, layout and compilation. Profile/job/PDF/model content is untrusted data, not authority.

## Sources and guided intake

- Imported PDF/narrative claims must start pending, preserving original text/source location and
  extraction uncertainty; an old resume is not automatically verified biography. PDF import remains
  unimplemented. Do not silently copy old “Present” dates or infer months, titles or employers.
- Ask neutral questions about skills actually used, where (class/project/job/research), personal
  contribution, supervision and limitations. Permit “not used” and uncertainty, not leading yes/no
  pressure from employer keywords. Never equate coursework with professional experience/proficiency.
- Record new answers as pending source statements, show them for explicit review and preserve
  provenance before permitting claim use. User confirmation is an assertion, not independent truth
  proof. No bulk “VERIFIED SKILLS” promotion, inferred metrics or automatic source migration.
- In 0.20.0, explicit **existing** skill/coursework source selection, cited current-plan contexts
  and neutral review questions are implemented by `review-content`. Answer capture/source intake,
  content attestations and assembly integration are not yet implemented; see
  [SECTION_CONTENT_REVIEW.md](SECTION_CONTENT_REVIEW.md).

## Before editing a resume

- Keep required/preferred distinctions, complete source quotes, alternatives and negation visible.
- A future requirement gap report should distinguish **candidate evidence for review**, **unknown/
  not documented**, **partially evidenced**, and **user-confirmed lack of experience**. Each entry
  needs source refs/context and remaining questions, not an unsupported “matched/satisfied” badge.
  Absence from a resume, a lexical match failure or missing model tag does not establish absence of
  experience. Existing retrieval supplies lexical candidates, not this semantic gap report.
- Propose wording, ordering and omissions with reasons **before applying them**. Respect mandatory/
  excluded content, never trim silently or call an unevaluated keyword count a relevance ranking.
  Automatic ranking and a consolidated change/omission report remain future work.
- Rephrase only supported facts. Preserve supervision, shared contribution, negation, uncertainty,
  prototypes and in-progress scope. A strong verb, tool/method, result or number is optional when
  source evidence does not support it. Never invent an outcome to complete a bullet-writing formula.
  Prefer plain specific wording; avoid unsupported “expert,” “passionate” or “results-driven” claims.
- Keep learning suggestions separate from past experience. A proposed class/project is future work,
  not a completed accomplishment or a way to imply a missing qualification is already held.

## Optional market research and rendering (not implemented)

- Market skills research is a separate optional operation, scoped by role/seniority/geography/date,
  with cited postings and an explicit sample. Do not claim “most postings” from an undefined sample,
  or transfer market keywords into candidate facts. No research/network/inference is implied here.
- Verify Jake's Resume license/attribution and pin an audited full template. Application rendering
  code, not an LLM or imported PDF, must control preamble/macros/escaping. Never execute untrusted
  LaTeX; use isolated compilation, no shell escape, resource limits and explicit tool prerequisites.
- One page and 1–2 lines per bullet are layout targets, checked after compilation, not prompt
  guarantees. Propose content cuts while preserving required material; never silently cut “weakest”
  bullets or shrink text to conceal conflicts. Compilation alone does not prove readable layout.
- `.tex` source and a compiled `.pdf` are separate artifacts. Require deliberate content/publication
  authorization and factual/visual review; component attestations do not authorize a finished resume.

These boundaries preserve local-only provider policy and the conservative wording default. No
provider activation, frozen evaluation rerun/tuning, PDF import, automatic ranking, history or
deployment was authorized by adopting this workflow. Implement one reviewable slice at a time.
