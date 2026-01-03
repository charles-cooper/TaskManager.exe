Mid-task handoff - save detailed context for next session.

1. Update the current task file with:
   - Attempts: what was tried, what failed
   - Summary: current state, key learnings, next steps
   - Notes: breadcrumbs (file:line references)
   - Make sure all relevant details are captured - these files are your only memory.
   - Ultrathink like a prompt engineer to provide all necessary info in the handoff prompt but context optimized.

2. Run: taskman sync "handoff: $ARGUMENTS"

3. Update STATUS.md with handoff context

The goal is to give the next session enough context to avoid repeating mistakes.
