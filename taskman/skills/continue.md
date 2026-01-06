Resume work from a previous session.

1. Run: taskman sync "continue"

2. Read STATUS.md - current focus, blockers, task index

3. Read the active task file(s) - focus on Summary and Notes sections

4. **Expand breadcrumbs selectively** (see below)

5. Ultrathink about your approach before continuing.

## Expanding Breadcrumbs

Task files contain pointers, not content. Expand only what's needed for your next step:

| Breadcrumb | Recovery |
|------------|----------|
| `src/auth.ts:45-80` | Read tool (those lines only) |
| run \`pytest -v\` | Bash tool (current state) |
| `jj diff -r @--` | Bash tool (last changes) |
| `issue: github.com/...` | WebFetch if needed |

**Order:** Read summary → identify next step → expand only what's needed → work → repeat.

Don't preload all references upfront. The previous session left good pointers - trust them and expand lazily.

**Ultrathink vs preloading:** Think deeply about *approach*, not by dumping all content into context. Expand breadcrumbs to answer specific questions, not "just in case".
