---
schema_version: 1
person:
  name: Alex Example
  email: alex@example.com
  phone: "+1-202-555-0100"
  location: Example City
  links:
    - https://example.com/alex
education:
  - id: edu_example
    title: Bachelor of Science in Computer Science
    organization: Fictional Example University
    start_date: "2023-09"
    end_date: "2027-05"
    details:
      - Expected graduation; all information in this file is fictional.
experiences:
  - id: exp_example
    title: Software Engineering Intern
    organization: Fictional Example Labs
    start_date: "2025-06"
    end_date: "2025-08"
    technologies: [Python, PostgreSQL]
    details:
      - Worked under supervision on an internal demonstration service.
projects:
  - id: proj_queue
    title: Demonstration Task Queue
    start_date: "2025-09"
    end_date: present
    technologies: [Python, SQLite]
organizations:
  - id: org_computing
    title: Computing Club Member
    organization: Fictional Example University
    start_date: "2023-09"
    end_date: present
research:
  - id: res_storage
    title: Undergraduate Storage Study
    organization: Fictional Example University
    start_date: "2025-01"
    end_date: "2025-05"
certifications:
  - id: cert_python
    title: Fictional Python Course Certificate
    organization: Example Training
    start_date: "2024-12"
    end_date: "2024-12"
awards:
  - id: award_demo
    title: Fictional Demo Day Award
    organization: Example Computing Club
    start_date: "2025-04"
    end_date: "2025-04"
additional_experience:
  - id: other_tutor
    title: Peer Programming Tutor
    organization: Fictional Example University
    start_date: "2024-09"
    end_date: "2024-12"
skills:
  languages: [Python, SQL]
  frameworks: [FastAPI]
  libraries: [pytest]
  tools: [Git]
  platforms: [Linux]
  other: [Technical writing]
coursework: [Data Structures, Databases]
accomplishments:
  - id: acc_api
    entry_id: exp_example
    statement: >-
      Implemented automated tests for 12 existing internal API endpoints under
      a mentor's review, checking both successful requests and invalid inputs.
    verified: true
    technologies: [Python, pytest]
    metrics:
      - 12 existing internal API endpoints covered by the added tests.
  - id: acc_queue
    entry_id: proj_queue
    statement: Implemented a local SQLite-backed task queue with retry handling.
    verified: true
    technologies: [Python, SQLite]
  - id: acc_queue_pending
    entry_id: proj_queue
    statement: Investigated whether batched writes could improve throughput.
    verified: false
verified_bullets:
  - id: bullet_api
    text: Added Python tests for 12 internal API endpoints under mentor review.
    accomplishment_ids: [acc_api]
---
# Fictional profile notes

This is demonstration data, not a real person's biography. Replace it only in your
private `data/profile/user_information.md`, never in this tracked example.

## exp_example

Rough notes: pair-programmed with a mentor. Do not imply ownership of the whole service.

## proj_queue

Résumé wording idea: explain the retry mechanism more concretely.
The throughput experiment has no verified result yet; do not invent a percentage.

```text
These notes, headings, and code fences are preserved, not promoted into verified facts.
```
