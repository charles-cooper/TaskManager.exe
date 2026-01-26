Prune and consolidate memory files, making them more context efficient.

Rule of thumb: keep MEDIUMTERM_MEM.md under 500 lines.

1. Read MEDIUMTERM_MEM.md and `ls topics/`

2. Evaluate each entry/file:
   - **Stale**: No longer applies → delete
   - **Redundant**: Duplicates another → merge or delete
   - **Too specific**: One-off that won't recur → delete
   - **Generalizable**: Similar entries → merge into pattern
   - **Too long**: Rewrite as pointers (see Progressive Disclosure in SKILL.md)

3. Reorganize structure as needed:
   - Split large topics
   - Merge small related topics
   - Adjust index to match
   - Create or merge directories

4. Update index in MEDIUMTERM_MEM.md to reflect the structure

5. Run: taskman sync "compact: <summary of changes>"

## Philosophy

Aggressive pruning > hoarding. Keep only:
- Hard-won insights (took multiple attempts)
- Non-obvious gotchas (would bite again)
- Patterns with validation paths

Delete:
- Obvious things (agent would figure out anyway)
- Stale info (no longer accurate)  
- Session-specific details (already in task history)
- Anything re-derivable from code/docs

The goal is a lean, high-signal memory that loads quickly and doesn't waste context.
