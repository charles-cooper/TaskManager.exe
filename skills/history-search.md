Search history for a pattern in diffs.

Arguments: <pattern> [--file <file>] [--limit N]

Pattern syntax (jj native):
- Default: glob match
- regex:pattern - regex match
- exact:pattern - exact match
- substring:pattern - substring match

Run: taskman history-search $ARGUMENTS

Display matching revisions.
