# Bounded IBM Bob task specification

## Target enhancement

Use IBM Bob to implement and verify a keyboard-accessible **review summary navigator** that lets a reviewer jump directly to:

- blocking findings
- warning findings
- rights-matrix rows requiring action
- the corrected-revision action
- the human-decision section

## Why this remains meaningful after Milestone 5

Milestone 5 establishes the accessible review page, findings, revision workflow, and export controls. The Bob task adds a new visible navigation layer rather than claiming work that was completed before Bob was activated.

## Constraints

- Do not change deterministic policy outcomes.
- Do not expose or import credentials, private evidence, or unrelated proprietary material.
- Do not introduce a second AI provider into the application runtime.
- Preserve security headers, revision safeguards, and the test suite.
- Add automated tests where practical and a documented keyboard verification checklist.

## Evidence package

Retain the initial Bob prompt, task history, changed files, diff, screenshots, and post-change test output. The final submission should state exactly what Bob changed and what was manually reviewed.
