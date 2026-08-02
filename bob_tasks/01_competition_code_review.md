# IBM Bob task 01: competition code review

Use Agent mode. Read `AGENTS.md` first.

Review the public CINE-GATE codebase against this issue:

> Verify that the hosted demo can show a complete rights-review workflow, that Google runtime calls are present in executable code, that errors fail safely, and that no credentials, private evidence, or unrelated proprietary material are exposed.

Required output:
1. a plan before changes
2. findings grouped by severity with file and line references
3. only approved fixes
4. exact test commands and results
5. `docs/IBM_BOB_EVIDENCE_01.md` containing task date, Bob version, files changed, commands run, findings resolved, and screenshots to retain

Do not access files excluded by `.bobignore`. Do not fabricate runtime evidence.
