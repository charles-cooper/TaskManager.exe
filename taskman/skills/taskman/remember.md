Persist knowledge to memory.

1. Choose destination:
   - Related to existing topic → update topics/TOPIC_<slug>.md
   - New topic area (3+ entries) → create topics/TOPIC_<slug>.md, add to index
   - Cross-cutting pattern → MEDIUMTERM_MEM.md
   - Architecture → LONGTERM_MEM.md

2. Use dense format. Key fields:
   - `problem:` / `fix:` - what and how
   - `check:` - command to verify (validation path)
   - `refs:` - file:line, other.md#section

3. If creating new topic, add entry to MEDIUMTERM_MEM.md index

4. Run: taskman sync "remember: <brief>"

## HOW > WHAT

Capture reasoning, not just conclusions:
- Bad: `fix: use async` 
- Good: `fix: use async | check: run bench.py (expect <2s) | refs: TOPIC_perf.md#async-test`

Include validation paths so next session can verify or update.
