Prune and consolidate memory files, making them more context efficient.

Rule of thumb: keep MEDIUMTERM_MEM.md under 500 lines.

1. Read MEDIUMTERM_MEM.md and `ls topics/`

2. Evaluate each entry/file:
   - **Stale**: Assumptions no longer hold → archive or delete (see below)
   - **Redundant**: Duplicates another → merge
   - **Too specific**: One-off that won't recur → archive
   - **Generalizable**: Similar entries → merge into pattern
   - **Too long**: Rewrite as pointers (see Progressive Disclosure in SKILL.md)

3. Reorganize structure as needed:
   - Split large topics
   - Merge small related topics
   - Adjust index to match
   - Create or merge directories

4. Update index in MEDIUMTERM_MEM.md to reflect the structure

5. Run: taskman sync "compact: <summary of changes>"

## Archive vs Delete

**Prefer archiving** - move to topics/_archive/ or tasks/_archive/.

**Delete only when assumptions no longer hold**:
- API changed, code rewritten, feature deprecated
- Architecture fundamentally different now
- The "why" behind the entry is obsolete

Age alone isn't enough - old knowledge can still be valid. The question is: **do the underlying assumptions still hold?**

When in doubt, archive. Archived files don't pollute context but can be recovered.

## Philosophy

Keep:
- Hard-won insights (took multiple attempts)
- Non-obvious gotchas (would bite again)
- Patterns with validation paths
- Recent learnings (even if uncertain - may prove valuable)

Archive:
- Old but possibly relevant (might need later)
- Superseded patterns (keep for historical context)
- Session-specific details not in task history

Delete:
- Assumptions no longer hold (the core deletion criterion)
- Obvious things (agent would figure out anyway)
- Already captured elsewhere (task history, code comments) - can be merged

The goal is a lean, high-signal memory that loads quickly and doesn't waste context.
