Resume work from a previous session.

Usage: `/continue <agent-slug>` (e.g., `/continue alice`, `/continue feature-x`)

1. Run: taskman sync "continue"

2. Read STATUS.md - task index, priorities, blockers (shared across agents)

3. Read handoffs/HANDOFF_<slug>.md - your session context, focus, next steps

4. Read the active task file(s) referenced in your handoff

5. Check MEDIUMTERM_MEM.md index - load only topics relevant to current task

6. **Expand breadcrumbs selectively** (see below)

7. Ultrathink about your approach before continuing.

## Expanding Breadcrumbs

Task files and topics contain pointers, not content. Expand only what's needed:

| Breadcrumb | Recovery |
|------------|----------|
| `src/auth.ts:45-80` | Read tool (those lines only) |
| `TOPIC_foo.md` | Read tool (if relevant) |
| run \`pytest -v\` | Bash tool (current state) |
| `jj diff -r @--` | Bash tool (last changes) |
| `issue: github.com/...` | WebFetch if needed |

**Order:** Read summary → identify next step → expand only what's needed → work → repeat.

Don't preload all references. Expand breadcrumbs to answer specific questions, not "just in case".
