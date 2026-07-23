# Design Pointer: Guru runtime acceptance and Full repair continuation

The Full design package is the design SSOT:

- [Package navigation](design-package/README.md)
- [Overview main definition](design-package/design-main.md)
- [Detail chapters](design-package/chapters/)

## Summary

The design combines a frozen Acceptance Closure contract with append-only runtime evidence and defect-class-based Full Repair Continuation. Runtime-required tasks remain active until current target-environment acceptance passes. Same-goal implementation defects return only to Phase 2; Detail, Overview, and Requirements are revisited only when evidence identifies the corresponding upstream owner.

The architecture is implemented through existing agent/Skill/workflow/spec and packaged-template contracts. Its Detail package is reviewed through the explicitly confirmed task-local CLI/framework profile in `research/framework-source-maintenance-detail-profile.md`, not through Flutter fallback taxonomy. It does not add task lifecycle states, parsers, reopen commands, automatic digest invalidation, or script-level archive enforcement. Every Trellis script remains explicitly forbidden by `gate-contract.json`.

## Current Phase

Requirements Gate remains confirmed and unchanged. The task is already
`in_progress`, but the current `OVERVIEW_DEFECT` pauses production edits and
returns only to Overview plus affected Detail. The corrected CLI/framework
Overview requires two fresh independent clean-context reviews and user
confirmation; after that, the affected Detail package requires two fresh
independent `directory_final` reviews and user confirmation against the
task-local profile. Do not rerun `task.py start`. This planning repair does not
authorize additional source, Integration, install, commit, archive, or other
lifecycle actions.
