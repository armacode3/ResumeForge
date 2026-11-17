# Resume-writing policy

Status: design policy for future pipeline phases. No application component loads or enforces
this file yet. Layout constraints will live separately in `config/layout.yaml` when rendering
is implemented.

## Evidence and truthfulness

- The validated user profile is authoritative; jobs and historical AI text are not sources of facts.
- Every generated claim must cite supporting accomplishment IDs and preserve their meaning.
- Never fabricate numerical impact, experience, dates, tools, responsibilities or accomplishments.
- Never imply ownership, leadership, production use or scale beyond the evidence.
- Use a metric only if explicitly verified, preserving units, scope, attribution and uncertainty.
- Flag missing or contradictory information. Ask the user rather than fill gaps with plausible details.
- Check claims deterministically where possible. AI factual review is supplementary and fallible;
  flagged/potentially unsupported claims require explicit user review, not silent approval.

## Job analysis and selection

- Separate required from preferred qualifications and responsibilities; identify evidence sought.
- Match demonstrated work and technical context, not keyword overlap alone.
- Prioritize direct relevance, specific verified accomplishments and strong supporting evidence.
- Respect user-mandated sections and experiences; report conflicts with space or truthfulness rules.
- Select projects demonstrating useful skills not already covered by stronger experience.
- Do not claim a job's technology merely because it appears in the job description.
- Explain selection/omission with concise evidence-based decision summaries.

## Bullet construction

- Prefer clear action–method–result phrasing; use XYZ, STAR or CAR when evidence supports it.
- Begin with accurate action verbs; name relevant technical implementation details concretely.
- Include verified results where available; a meaningful qualitative result is better than an invented metric.
- Condense rough notes without upgrading responsibility, changing causality or losing important qualifiers.
- Use job terminology naturally only when it truthfully describes the documented experience.
- Avoid vague claims, buzzword stuffing, repetitive accomplishments and redundant bullets.
- Keep tense and naming consistent; retain accurate dates and tool names.

## Sections, ATS readability and review

- Initially target one-page CS internship resumes with contact information, education, relevant
  experience/projects, and technical skills as supported by the profile and user requirements.
- Prefer standard section names, selectable text, uncomplicated structure and meaningful ordering.
- Do not imply that formatting heuristics guarantee compatibility with every ATS.
- Remove redundancy and low-priority content before shrinking typography; honor readability limits.
- Report unsupported requirements as gaps, never secretly add them to the resume.
- Require a final human factual and visual review. Page count alone does not establish quality.
