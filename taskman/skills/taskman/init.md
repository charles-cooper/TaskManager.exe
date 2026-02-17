# /init

Initialize `.agent-files/` in the current project directory.

## When to use

First time setting up taskman in a project. Creates the jj-backed scratch space for agent memory, tasks, and handoffs.

## Steps

1. Run `taskman init` in the project root
2. Add `.agent-files/` to `.gitignore` if not already present
3. Populate initial files:
   - `STATUS.md` - current focus, active tasks, blockers
   - `LONGTERM_MEM.md` - architecture knowledge (stable, rarely changes)
   - `MEDIUMTERM_MEM.md` - patterns index, cross-cutting learnings
4. Create `tasks/` directory for task files

## What it does

```
taskman init
```

- Creates `.agent-files/` as a standalone jj git repo
- Sets agent author identity (`Agent <agent@localhost>`)
- Creates initial empty files: STATUS.md, LONGTERM_MEM.md, MEDIUMTERM_MEM.md, tasks/
- Creates a `default` bookmark and starts fresh working copy

## After init

- Add `.agent-files/` to project `.gitignore`
- For remote backup: `jj git remote add origin <url>` inside `.agent-files/`
- Start populating STATUS.md with current project context
- Use `/remember` to persist learnings as you work

## Errors

- **`.agent-files already exists`**: Already initialized. Use existing workspace.
- **jj not installed**: taskman requires jj. Install from https://github.com/martinvonz/jj
