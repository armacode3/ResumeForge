# Local Ollama integration

## What is implemented

`analyze-job --provider ollama` sends a selected local job to an already running, local-only
Ollama server. The model fills the existing JSON schema; the engine applies the same strict
schema, ID, literal-text and source-quotation checks as fake replay. No candidate profile is
loaded implicitly, no tools are supplied or executed, and no biography is approved or generated.

The initial target is **Qwen3:4b** (Q4_K_M, approximately 2.5 GB of weights). It requires more
memory during inference than its download size, and CPU execution may be slow. This is a
starting point for evaluation, not a guarantee that a small model will extract every job correctly.

## Install and start separately

Install Ollama for your platform using the [official instructions](https://docs.ollama.com/linux).
ResumeForge never installs a runtime, downloads/pulls models, changes system services, or
edits Ollama configuration. Runtime/model setup is a separate operator action. Keep model files
outside Git; downloading weights needs internet/disk space but not a paid inference subscription.
Local execution still consumes hardware resources and electricity.

For a manual Linux/WSL server, start this in a separate terminal:

```bash
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11434 ollama serve
```

Then download the model explicitly and inspect its tag:

```bash
ollama pull qwen3:4b
ollama list
```

If an existing Ollama service already owns the port, do not start another server or overwrite
its configuration blindly. Either restart that service with cloud disabled using the official
platform instructions, or run a separate loopback instance on another port. Both the Ollama
CLI and ResumeForge must target that port:

```bash
# Server terminal:
OLLAMA_NO_CLOUD=1 OLLAMA_HOST=127.0.0.1:11435 ollama serve
# Model setup terminal:
OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen3:4b
# ResumeForge terminal:
resumeforge analyze-job --job examples/jobs/backend_intern.md \
  --provider ollama --ollama-port 11435 --timeout 600
```

Stop a manual server with Ctrl+C in its terminal. There is no ResumeForge autostart service.
In WSL, running the server in the same Linux environment avoids changing network bindings to
reach a Windows-host service. Do **not** expose the API on `0.0.0.0` just to make it reachable.

This integration requires `/api/status` with a strict boolean `cloud.disabled: true`, plus
`/api/show` local-model metadata. An older server without these APIs is rejected; upgrade
rather than bypassing the checks. The evaluation runtime used Ollama **v0.40.16**.
The application does not pin/install that binary. Review upstream releases for a durable setup.

## Run job analysis

```bash
source .venv/bin/activate
resumeforge analyze-job --job examples/jobs/backend_intern.md \
  --provider ollama --model qwen3:4b
```

Omit `--mock-response` for local inference. Fake remains the default provider and still requires
its explicit response fixture; no command silently switches between fake, local or cloud.
Missing models produce an error with no automatic pull. Conflicting provider options are errors.

The command emits only validated `JobAnalysis` JSON to stdout. Progress/errors go to stderr.
Save real analyses only under ignored private storage, for example `artifacts/job_analysis.json`.
Check exit status before treating a redirected file as valid; a failed command can leave it empty.

## Runtime options and limits

| Option | Default | Allowed / behavior |
| --- | --- | --- |
| `--provider` | `fake` | `fake` or explicit `ollama`; no cloud adapter. |
| `--model` | `qwen3:4b` | Local model tag, at most 128 characters, not a URL/path or cloud tag. |
| `--ollama-port` | `11434` | Integer 1–65535; host is fixed to `127.0.0.1`. |
| `--timeout` | `180` | 1–600 seconds, shared client deadline and per-I/O timeouts. |
| `--max-output-tokens` | `4096` | Integer 128–8192; token-limit/incomplete output is rejected. |

The adapter uses a 16,384-token context, temperature/seed 0, `think: false`, non-streaming
generation, and `keep_alive: 0` to unload after each request. These settings reduce variability
and memory retention; they do not guarantee identical or correct answers across model/runtime
versions. Cold model loads contribute to latency.

Before any HTTP call, a conservative context check reserves output tokens plus 1,024 tokens
of overhead and treats UTF-8 input/schema bytes as an upper-bound token estimate for this
initial byte-level model. Oversized jobs fail; no input is silently truncated or chunked.
This is not a universal tokenizer-count guarantee for arbitrary custom models.
Lowering output limits can leave more input budget but may truncate the answer. Large-job
chunking/tokenization needs a separate tested feature rather than removing source material silently.

Connect/write/pool waits are capped at five seconds. A monotonic deadline is checked before
each API call and between response chunks; remaining time bounds each read operation.
This is client-side protection, not a hard process/resource sandbox: I/O scheduling can overrun
the nominal deadline, and cancelling a client request does not prove model computation stopped.
There is no automatic retry or corrective second model call.

Every API response envelope is capped at 1 MiB and compressed responses are rejected. Malformed
JSON/duplicates/nonstandard constants, incomplete generation, unexpected models/roles and tool
calls fail closed. The adapter does not log/echo raw API envelopes, error bodies, transport details
or thinking traces; only assistant content is passed to the engine. That content must still pass
the existing response/quotation limits. Server-side logging is a separate operator responsibility.

## Local-only boundary

For each inference the adapter:

1. Calls `GET /api/status` and requires `cloud.disabled` to be boolean true.
2. Calls `POST /api/show` with only the selected model name. Requires GGUF/completion metadata,
   with no `remote_host` or `remote_model`, including aliases that might otherwise hide cloud use.
3. Only after those checks, calls `POST /api/chat` with trusted instructions/schema separately
   from the selected untrusted job text. No profile or tool registry is included.

HTTPX uses a literal loopback host, no environment proxies (`trust_env=False`), and no redirects.
There is no remote-base-URL option; `OLLAMA_HOST` in the ResumeForge process cannot redirect it.
Cloud features must be disabled **on the Ollama server**, not merely in the caller's environment.
The server's status response is a guard against accidental cloud use, not cryptographic
attestation: this design trusts the local process/OS and cannot prove a malicious proxy is honest.
You remain responsible for secure server binding, machine access and log/storage permissions.

## Validation and model quality

Structured generation constrains JSON shape, not factual interpretation. Exact source checks
can still reject invented/normalized terms, and passing checks cannot prove correct classification
or complete extraction. Do not repair a failed quotation by weakening validation or silently
substituting text. Review the model response/prompt and improve with synthetic regression cases.

All normal tests use mocked HTTP or a synthetic loopback HTTP server, **not** Ollama or real
models. CI does not download weights or run inference. The command above is an explicit opt-in
live smoke test; start with fictional jobs, then manually review required/preferred distinctions,
missing metadata and coverage. A few successful examples are not a general quality benchmark.

Model tags can change their weights over time. For reproducible evaluations record the Ollama
version, `ollama list` model digest, prompt version, settings and source hash. Current analysis
metadata stores the requested model tag and prompt version, not a pinned weight digest.

## Initial live evaluation (not an accuracy certification)

Evaluation used Ollama v0.40.16 and Qwen3:4b digest prefix `359d7dd4bcda`, only fictional jobs,
prompt `job-analysis-v3`, 16,384 context / 4,096 output tokens, and a 600-second client budget.
Runtime/model download and execution were explicitly performed for this development session,
not added as application/CI behavior. No private profile was sent and no system service was changed.

| Source | Schema/quote and basic metadata checks | Observed wall time |
| --- | --- | --- |
| `examples/jobs/backend_intern.md` | Passed; 9 extracted items | About 80 seconds |
| `examples/jobs/missing_metadata.txt` | Passed; absent company/title remained null; 5 items | About 59 seconds |

These timings describe one WSL session, not a performance guarantee. Earlier prompt iterations
failed casing/quotation checks and emitted empty metadata instead of null or reused IDs. The
validators were kept strict; prompt/schema descriptions were refined and regression tests added.

Manual review still found incomplete tagging: automated testing was missing from backend concept
tags, and SQL was missing from language tags in the other case, though those phrases remained in
their qualification lists. Hand-authored `.response.json` fixtures are separate expectations,
not a claim that the local model reproduces them. Broader recall/classification evaluation is
needed before relying on these tags for ranking. No additional model or cloud fallback was pulled.

The later [six-case single-pass review](evaluations/qwen3-4b-v3.md) used the same model/prompt
without retries: all six responses validated, none exactly matched the references. Incomplete
tags and lost known metadata remain limits; local inference is not approved for unattended ranking.

References: [structured outputs](https://docs.ollama.com/capabilities/structured-outputs),
[local FAQ / disabling cloud](https://docs.ollama.com/faq),
[Qwen3:4b](https://ollama.com/library/qwen3:4b).
