# Job analysis — Phase 2 contracts

## Status: fake replay and explicitly selected local Ollama

ResumeForge loads a local job description, builds a provider-neutral structured request,
validates the returned requirements, and checks literal quotations against that exact job.
**FakeProvider** replays a JSON response you supply; it does not extract requirements.
**OllamaProvider** performs real local inference through a guarded loopback server. See
[OLLAMA.md](OLLAMA.md) for installation, local-only policy, limits and opt-in evaluation.

There is no paid/cloud provider, API key, remote-base-URL setting, URL ingestion, resume matching
or generation. Local analysis is a model interpretation, not proof of correct/complete extraction.
No candidate/profile input is needed. Existing provisional profile facts remain unchanged.

## Run the fictional example

```bash
resumeforge analyze-job \
  --job examples/jobs/backend_intern.md \
  --mock-response examples/jobs/backend_intern.response.json
```

The response fixture is hand-authored fictional data. Passing a different job does **not**
make this fixture adapt to it. Absent source quotations fail validation; even quotations shared
between two jobs do not establish that replayed categories are correct or complete.

Success writes one JSON document to **stdout**, and an explicit offline/fake notice to **stderr**.
Failures emit an actionable error to stderr and no partial JSON to stdout. Exit codes:
0 = validated result; 1 = file/provider/JSON/schema/quotation failure; 2 = CLI usage error.
`--job` is required. Default fake mode requires `--mock-response`; local inference requires
`--provider ollama` instead, and cannot be combined with a mock response. There is no fallback.

The command itself creates no files. To retain a result, use private ignored storage:

```bash
mkdir -p artifacts
resumeforge analyze-job \
  --job examples/jobs/backend_intern.md \
  --mock-response examples/jobs/backend_intern.response.json \
  > artifacts/job_analysis.json
```

Real job descriptions/analyses may contain proprietary or personal information. Keep them
under ignored `data/jobs/` and `artifacts/`, not in tracked examples. The stdout JSON deliberately
contains selected job text and quotes; do not post it to public logs without review.
Shell redirection can create an empty file on a failing command, so check the exit status.

## Inputs and limits

- Job and mock-response files must be regular local UTF-8 files, each at most **1,048,576 bytes**.
- File extensions are not enforced. Plain text and Markdown work; there is no PDF/HTML parser
  or URL fetching. A URL passed as a path is not fetched.
- Job text cannot be blank, contain only a leading BOM/whitespace, or contain NUL characters.
- Exact decoded source, optional UTF-8 BOM, Unicode and line endings are preserved. The source
  hash is SHA-256 of the original UTF-8 bytes; changing line endings changes the hash.
- JSON allows a leading UTF-8 BOM. Duplicate keys (including escaped equivalents), NaN/Infinity,
  Markdown fences, multiple documents, excessive integer sizes and nesting beyond 32 containers
  are rejected. Decoder recursion failures are also handled without dumping input.
- Fact text and each quote are nonblank strings, at most 8,192 characters. Each category contains
  at most 200 items. Unknown fields, wrong types and unsupported schema versions fail validation.

## Structured requirements, schema version 1

Every field is explicit; omitted categories are errors rather than silently assumed empty:

| Field | Shape and meaning |
| --- | --- |
| `schema_version` | Integer 1, not a boolean/string. |
| `company`, `job_title` | `null` if not identified; otherwise `{text, source_quote}`. |
| `responsibilities` | Job duties and expected work. |
| `required_qualifications` | Required credentials, skills or experience. |
| `preferred_qualifications` | Preferred, not mandatory qualifications. |
| `programming_languages` | Explicitly mentioned languages. |
| `frameworks` | Explicitly mentioned frameworks. |
| `technical_concepts` | Relevant technical concepts such as testing or HTTP APIs. |
| `domain_terms` | Job-specific industry/domain terminology. |
| `evidence_sought` | Explicit demonstrations/examples sought by the employer. |

Each list item is `{id, text, source_quote}`. IDs use `job_` followed by lowercase ASCII
letters/digits/underscores, at most 80 characters total, and are unique across all categories.
Keep them stable when manually revising a fixture; the engine does not generate or renumber IDs.
Case-insensitive duplicate item text within a category is rejected. The same quoted term may
appear in different categories with different IDs when it serves different purposes.

`text` must occur **exactly** within `source_quote`; the quote must occur **exactly** within the
selected job. Case, qualifiers, punctuation and whitespace matter. Initial extraction is literal,
not a paraphrased summary. A shorter exact quote is preferable to changing line endings to fit.

These checks establish traceability, **not semantic truth, correct classification, completeness,
authenticity of the employer, or resistance to every prompt-injection attempt**. For example,
a framework tag alone does not establish it is required; review the qualification categories
and source. A fact can be copied from the wrong context despite passing substring checks.
Review every analysis, including fake/previously approved responses.

## Result and provenance

The stdout `JobAnalysis` contains:

- `schema_version: 1` and `source_sha256`.
- `provider`/`model` (`fake` / `fixture-v1` for replay; `ollama` / requested tag for local inference).
- `prompt_version` (`job-analysis-v3`).
- `requirements`: the validated extraction described above.
- `warnings`: always a review reminder, plus flags for unidentified company/title and no items.

Missing metadata is not inferred. An all-empty extraction is allowed with warnings because the
validator cannot prove what a model should have found. It is not a guarantee of usable analysis.

## Python interface and dependency injection

```python
from pathlib import Path
from resumeforge.jobs import analyze_job, load_job
from resumeforge.providers import FakeProvider

document = load_job(Path("examples/jobs/backend_intern.md"))
provider = FakeProvider.from_file(Path("examples/jobs/backend_intern.response.json"))
analysis = analyze_job(document, provider)
```

`JobDocument(text)` supports callers without file I/O. Loading raises `InputError`; analysis
failures raise `JobAnalysisError`. Ollama configuration/adapter failures raise safe `ProviderError`
messages, preserved by the engine as actionable analysis errors. `StructuredOutputProvider` is a
Python `Protocol`: any trusted
adapter implementing `name`, `model` and `complete(request) -> str` can be injected. The request
separates trusted versioned instructions, untrusted job text, and a Pydantic-generated JSON schema.
No candidate data or tool registry is included. Engine validation applies to every adapter response.

One provider call is made per analysis, without automatic retry. Provider exceptions are sanitized;
bad JSON/schema/quotes fail closed. The supplied fake completes immediately and performs no network
I/O. The Ollama adapter has explicit local-only guards, time/output/context/response limits and
no cloud fallback; this synchronous provider protocol alone does not impose those protections.

## Local inference and next gates

The user selected local-only Ollama with Qwen3:4b. Normal tests remain mocked, including failures
and multiple layouts. Model evaluation must be explicit and distinguish syntax/source grounding
from semantic accuracy and completeness. Before any future cloud adapter, agree on provider,
data disclosure, credentials, costs and time/failure policy; never infer authorization from a key.
