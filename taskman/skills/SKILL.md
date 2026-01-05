---
name: taskman
description: Task management for AI agents. Use for session handoffs (/continue, /handoff), task completion (/complete), syncing .agent-files (/sync, /describe), and searching history (/history-search, /history-diffs, /history-batch).
---

# Taskman

Task management CLI for AI agents with version-controlled .agent-files.

## Commands

| Command | Use when |
|---------|----------|
| /continue | Resuming work from a previous session |
| /handoff | Saving context mid-task for next session |
| /complete | Finishing and archiving a task |
| /sync | Syncing .agent-files with origin |
| /describe | Creating a named checkpoint |
| /history-search | Searching history for patterns |
| /history-diffs | Viewing diffs across revisions |
| /history-batch | Fetching file content at revisions |

When a command is invoked, read the corresponding `.md` file in this skill directory for detailed instructions.
