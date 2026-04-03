---
name: example-skill-name
description: Use when handling a recurring workflow that benefits from fixed steps, clear validation, and reusable references or scripts.
---

# Example Skill

## When to use

Use this skill when:
- the task appears repeatedly
- the workflow is multi-step
- correctness depends on doing steps in the right order
- you want stable validation instead of ad hoc reasoning

Do not use this skill when:
- the task is a one-off
- a simple prompt rewrite is enough
- there is no repeated workflow to standardize

## Goal

State the concrete outcome this skill is meant to achieve.

Example:
- break a large webhook into modules safely
- run staged archive flows without race conditions
- manage AI prompts and skills through stable interfaces

## Workflow

1. Understand the user request and identify the exact sub-flow.
2. Inspect only the files needed for that sub-flow.
3. Make the smallest safe code change first.
4. Add or update targeted tests.
5. Run fast validation before broader regression.
6. Summarize outcome, affected files, and residual risks.

## Key rules

- Preserve existing behavior unless the task explicitly changes it.
- Prefer incremental refactors over broad rewrites.
- Keep LINE flow, web flow, and API flow behavior aligned.
- If stateful flows are involved, always consider race conditions and stale state cleanup.
- If UI choices can be constrained, prefer dropdowns over free text.

## Validation

Minimum validation:
- `python -m py_compile ...`
- targeted unit tests for the changed path

Broader validation when the change touches shared routing:
- LINE command validation
- web direct button validation
- web form validation

## Files to inspect first

- `agents/...`
- `tests/...`
- `docs/...` when behavior contracts are documented there

## References

Add references here when the skill grows:
- `references/workflow.md`
- `references/validation.md`
- `references/domain_rules.md`

## Scripts

If the workflow becomes repetitive, prefer adding scripts under:
- `scripts/`

Example:
- `scripts/run_fast_validation.py`
- `scripts/rebuild_prompt_index.py`

## Output expectations

Your final response should include:
- what changed
- where it changed
- what was validated
- any remaining caveats
