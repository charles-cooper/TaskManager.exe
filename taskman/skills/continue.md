Resume work from a previous session.

1. Run: taskman sync "continue"

2. Read STATUS.md - current focus, blockers, task index

3. Read the active task file(s) - focus on Summary and Notes sections

4. Check MEDIUMTERM_MEM.md index - load only topics relevant to current task

5. **Expand breadcrumbs selectively** (see below)

6. Ultrathink about your approach before continuing.

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
