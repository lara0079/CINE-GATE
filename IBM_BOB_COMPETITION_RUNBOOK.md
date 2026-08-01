# IBM Bob competition runbook

## Purpose

Produce truthful, reviewable evidence that IBM Bob was meaningfully used in the CINE-GATE development process without giving Bob access to credentials, private evidence, archives, or unrelated proprietary material.

## Before opening the workspace

1. Use a clean copy of the public CINE-GATE repository only.
2. Confirm `.bobignore` is present.
3. Confirm no `.env`, credential file, database, archive, private evidence, or unrelated proprietary file is inside the workspace.
4. Read `AGENTS.md`.
5. Disable broad auto-approve settings. Review each proposed command and edit.

## Required evidence set

Retain screenshots or screen recording showing:

- IBM Bob identity and version
- the CINE-GATE workspace
- the task prompt
- Bob's plan before edits
- reviewed code changes
- commands and test results
- Bob Findings or review results
- final evidence note committed to the repository

Do not reveal API keys, personal data, file-system paths outside the public repository, or private material.

## Recommended task order

1. Run `bob_tasks/01_competition_code_review.md`.
2. Review findings manually.
3. Approve only bounded changes that preserve `AGENTS.md`.
4. Run all tests and the quality gate.
5. Commit the resulting evidence note.
6. Run `bob_tasks/02_agent_trace_polish.md` only if additional interface polish is still needed.

## Claims allowed after completion

The submission may state only what the retained evidence proves, for example:

> IBM Bob was used to review and improve the public CINE-GATE codebase, execute an approved bounded task, and verify the resulting changes through the documented test suite.

Do not claim that Bob created the entire architecture or any feature it did not actually create or modify.
