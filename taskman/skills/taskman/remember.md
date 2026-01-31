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

Capture *how you arrived* at conclusions - the exact steps are often more valuable than the answer:

- **Bad**: `fix: use async`
- **Bad**: `investigated: profiler showed blocking I/O` (what profiler? what command?)
- **Good**:
  ```
  repo: github.com/org/myapp @ a1b2c3d (2024-01-15)
  problem: 5s latency on /api/fetch
  debug steps:
    1. `pip install py-spy` (v0.3.14)
    2. `sudo py-spy record -o profile.svg -- python server.py` → 80% time in requests.get()
       (needed sudo for process attach; svg at ./debug/profile.svg)
    3. `curl -w "%{time_total}\n" http://localhost:8000/api/fetch` → 5.2s
    4. `grep -n "requests.get" src/fetch.py` → 10 calls, lines 42-51
    5. hypothesis: serial blocking. 10 × 0.5s = 5s matches observed latency
  root cause: sync requests serialized
  fix: asyncio.gather() for parallel fetches → commit b2c3d4e
  verify: `python bench.py` → 0.6s (was 5.2s)
  refs: src/fetch.py:42-51, src/api.py:100, TOPIC_perf.md#async-pattern
  ```

Capture exact commands, flags, output snippets. Future sessions can re-run to verify assumptions still hold.

**Anchor to codebase state**: include commit hashes, file:line refs so future sessions can detect drift:
```
at commit: a1b2c3d (2024-01-15)
refs: src/fetch.py:42-51, src/api.py:100
```
If code has changed since recorded commit, re-verify before trusting conclusions.
