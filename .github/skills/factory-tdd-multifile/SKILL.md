---
name: factory-tdd-multifile
description: Implement or verify a CODEN Factory code change with RED-GREEN TDD, bounded multi-file acceptance, hidden cases and immutable evidence. Use for genuine engineering tasks, not speculative demos.
---
# CODEN Factory — Test-driven multi-file engineering

## Trigger
Use for any behavior-changing PR, agent coding task, bug, or multi-file project slice. **DRAFT** reusable instructions only.

## Steps
1. Identify real checked-in code, stack, test conventions and exact expected outputs. Preserve existing controls; never rewrite them merely to make CI pass.
2. Write RED tests first. Run focused tests, record observed expected failure and the commit/run ID. A mock/fake agent passing contract tests does **not** prove a real model session.
3. Implement the smallest GREEN change. Prefer reused open-source components and templates already vetted; avoid new dependencies. Run focused, then project-wide contract tests.
4. For an agent-generated candidate, isolate the workspace, limit permitted paths and invoke only an explicitly authorized local provider; stop with BLOCKED if prerequisites fail. Do not bypass OpenHands issue #162. Capture model identity, elapsed/resource budget and actual invocation evidence.
5. Independently inspect **every generated file** and run visible plus hidden acceptance cases. The hidden tests must be withheld from prompts. Run syntax, formatting, security and no-secret checks; never execute candidate code outside an approved sandbox.
6. Produce a read-only candidate package with hashes and audit log, then a Draft PR (not direct commits to protected `main`).

## Definition of done
A real multi-file trial needs model execution evidence, correct file topology, independent acceptance of code (not its own tests alone), and safe teardown. Do not claim successful OpenHands execution based on mocked SDK tests (#149). Human review, **no automatic merge**, no hidden release permission, no paid calls, no production deployment.
