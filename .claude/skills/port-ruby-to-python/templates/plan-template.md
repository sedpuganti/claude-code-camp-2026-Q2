# Python Port Plan — NN · <Step Name>

<!--
Fill in NN (zero-padded step number, e.g. 05) and <Step Name> (title-cased,
matching the Ruby step's folder name minus the number, e.g. "Agent Loop" for
05_agent_loop). Delete every HTML comment in this template once its section
is filled in — none should survive into the final doc.
-->

## Goal

<!--
2-4 sentences:
- Name the exact source/target folders: "Port week1_baseline/ruby/<NN_new> to
  Python as week1_baseline/python/<NN_new>, preserving the Ruby step's public
  surface and example behaviour."
- State plainly that the target folder already exists as an unmodified copy
  of the previous Python step (confirmed via `diff -rq`), and that this plan
  covers only the step delta.
- One sentence on the single new concept/capability this step adds (e.g. "a
  Boukensha::Client that POSTs a payload and retries on transient failure").
- If there's anything this step must explicitly NOT do (e.g. no formal test
  suite, no fixing a known-but-deferred issue), say so here — later sections
  will elaborate, but stating the boundary up front prevents scope creep.
-->

## Reference files (source of truth — read these before porting)

<!--
Table 1: every Ruby file that changed in this step's diff, with its role.
Include the step's README.md first (it's always the spec doc), then each
changed lib file, the top-level lib/boukensha.rb require list, the example,
and the Ruby launcher (bin/ruby/<NN_new>) as a shape reference for the new
Python launcher.
-->

| Ruby file | Role |
|---|---|
| `week1_baseline/ruby/<NN_new>/README.md` | Behaviour/spec doc for this step |
| ... | ... |

<!--
Table 2: files with zero diff between <NN_prev> and <NN_new> — list them so
it's explicit they're compare-only, not part of this port's scope. Confirm
via `diff -rq` before writing this table, don't guess.
-->

Unchanged from step <N-1> (compare only, do not re-port unless drift is found):

| Ruby file | Note |
|---|---|
| ... | No diff |

<!--
Table 3: the existing Python files this plan will touch or explicitly leave
alone, tied to the actual <NN_new> folder that already exists as a copy.
-->

Existing Python snapshot to modify:

| Python file | Role |
|---|---|
| `week1_baseline/python/<NN_new>/` | Currently an unmodified copy of the `<NN_prev>` Python port; apply the step delta here |
| ... | ... |

## Design Considerations

<!--
One bullet per non-obvious translation decision. Each bullet should be
self-contained enough that someone reading only this plan (not the Ruby
source) understands the *why*, not just the *what*. Cover, where relevant:
- Any Ruby idiom with no 1:1 Python equivalent, and the specific resolution
  chosen (see SKILL.md's "Common recurring ones" list for the standard
  playbook — reuse that phrasing/resolution rather than re-deriving it).
- Whether anything in this step's diff looks like a bug fix vs. a bug
  introduction on the Ruby side, and what the Python port should do about it
  (default: port real fixes, flag-don't-silently-reproduce regressions, ask
  in Open Questions if unsure).
- Confirmation that no new dependencies are needed (or exactly which stdlib
  modules cover what an external Ruby gem was doing), since this repo
  deliberately stays dependency-minimal.
- Explicit callout of anything intentionally NOT changing that a careless
  read of the Ruby diff might tempt someone to "fix" anyway.
-->

## Target file layout

<!--
A file tree of week1_baseline/python/<NN_new>/ with inline comments marking
which files are `# new`, `# updated: <what changed>`, or unmarked (meaning:
unchanged carryover from <NN_prev>). End with the new launcher path.
-->

```
week1_baseline/python/<NN_new>/
  ...
week1_baseline/bin/python/<NN_new>
```

## Porting notes (Ruby → Python mapping)

<!--
One subsection per changed file, in dependency order (errors/config before
the things that raise/read them; base classes before subclasses; the
top-level __init__.py exports last before the example). For each:
1. A `### <Concept> (<ruby_file> → <python_file>)` heading.
2. The relevant Ruby source snippet (only the changed/new parts — no need to
   reproduce unchanged surrounding code).
3. The Python target snippet, complete enough to implement directly from.
4. A bullet list of specific translation notes: symbol→string mappings,
   `.fetch` vs `[]`/`.get` semantics and their differing failure modes,
   keyword-only vs positional-or-keyword decisions (and why — check this
   port's established convention of avoiding Python's `*,` keyword-only
   syntax unless Ruby's own call sites force it), error-class hierarchy
   mapping (`StandardError` → `Exception`), and anything about parameter
   ordering that differs from Ruby because Python enforces defaults-last.
-->

### Errors (`errors.rb` → `errors.py`)

...

## Configuration Schema

<!--
Almost always unchanged from the previous step — copy it forward verbatim
rather than re-deriving it, and say "Unchanged from steps 0-<N-1>." If this
step's diff *does* change settings.yaml's shape, show the new shape and call
out exactly what changed.
-->

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: true
mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

## Implementation Steps

<!--
A numbered checklist mirroring the Porting Notes subsections in dependency
order, ending with adding the launcher and running the smoke test through
it. This is the literal to-do list for step 6 in SKILL.md — keep it concrete
enough to execute without re-reading the Porting Notes for each item.
-->

1. Confirm the existing `week1_baseline/python/<NN_new>` snapshot is still an
   unmodified copy of `<NN_prev>` (README/example still say the old step
   number).
2. ...
N. Add `week1_baseline/bin/python/<NN_new>` (using this skill's
   `templates/launcher.sh`) and make it executable.
N+1. Run the smoke test through the launcher.

## Verification

<!--
The exact launcher command, any preconditions (env vars, API keys,
settings.yaml requirements — note explicitly whether this step needs a
*working* API key because it makes a real network call, vs. a placeholder
being fine because it doesn't), and a bullet checklist of expected
stdout/exit-code/exception behavior specific enough that running the command
and eyeballing the output is sufficient to confirm the port is correct.
End with "No `pytest` suite is required for this step." unless the user has
changed that decision.
-->

Run:

```bash
./week1_baseline/bin/python/<NN_new>
```

Expected checks:

- exits with status 0
- ...

No `pytest` suite is required for this step.

## Open Questions

<!--
Only real judgment calls — see SKILL.md's guidance on what qualifies. Number
them, bold a short title, then 2-4 sentences of context on why Python can't
just do what Ruby did and what the candidate resolutions are. Leave a blank
line after each question for the user's inline answer (this repo's
established interaction pattern: the user writes a one-line answer directly
under the question, often terse — "do what you have to make it work", "fix
it"). Don't pre-answer these yourself; that defeats the point of asking.
-->

1. **<Short title>.** <Context and candidate resolutions.>
