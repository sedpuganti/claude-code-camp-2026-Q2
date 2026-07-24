---
name: port-ruby-to-python
description: Port the next (or a specified) BOUKENSHA Ruby tutorial step in week1_baseline/ruby/ to its Python snapshot in week1_baseline/python/, following this repo's established delta-porting workflow (diff the two Ruby steps, write a plan doc under docs/plans/python_port/, get the user's sign-off on Open Questions, implement only the delta, wire up the launcher, run the smoke test). Use this whenever the user asks to "port the next ruby step", "port step NN to python", "continue the python port", or mentions porting/translating a week1_baseline Ruby step to Python — even if they just name a step number or say "do the next one." Do NOT use this for general Ruby-to-Python translation outside week1_baseline, or for writing brand-new Python features that have no Ruby counterpart.
---

# Port Ruby step to Python

BOUKENSHA is a Ruby tutorial built as a sequence of numbered, self-contained
snapshot steps (`week1_baseline/ruby/00_config`, `01_struct_skeleton`,
`02_the_registry`, `03_prompt_builder`, `04_api_client`, ...). Each new Ruby
step is a small delta on the previous one. We're mirroring that sequence in
Python, one step at a time, into `week1_baseline/python/<NN_stepname>/`.

The core discipline of this workflow: **never re-derive a whole step from
scratch, and never "fix" Ruby's quirks along the way.** Every Python step
folder starts as a literal copy of the previous Python step folder, and only
the exact Ruby delta for the new step gets applied on top. This keeps each
port small, reviewable, and faithful — a step that ports a bug faithfully is
correct; a step that "improves" on Ruby has silently diverged and will bite
later when Ruby's own step N+1 depends on Ruby's step N behaving exactly as
written. If Ruby itself fixes something in this step's diff, port the fix.
If Ruby carries a wart forward unfixed, carry it forward too, and note it.

Five completed plans already exist under `docs/plans/python_port/` (`00_config`,
`01_struct_skeleton`, `02_the_registry.md`, `03_prompt_builder.md`,
`04_api_client.md`). **Read at least the two most recent ones before writing a
new plan** — they show the exact tone, level of detail, and the specific Ruby
idioms (keyword-arg ordering, symbols, `attr_reader`, `method_missing`-free
duck typing, `StandardError` hierarchies) that keep coming up and how prior
plans resolved them. Don't reinvent those resolutions; reuse them.

## Workflow

Work through these phases in order. Don't skip ahead to implementation before
the user has weighed in on Open Questions — that's the one hard gate in this
process, because some of those questions encode judgment calls Python simply
cannot make identically to Ruby (see "Open Questions" below).

### 1. Resolve which step you're porting

If the user named a step (e.g. "port `05_agent_loop`" or just `05`), use it.
If they said "next" or didn't specify, detect it:

```bash
ls week1_baseline/ruby/          # numbered step dirs, source of truth
ls week1_baseline/python/        # numbered step dirs already started
ls docs/plans/python_port/       # plan docs already written (one per completed step)
```

The next step is the lowest-numbered Ruby step that has no plan doc yet under
`docs/plans/python_port/`. Confirm your guess with the user in one line
before proceeding if there's any ambiguity (e.g. a python folder exists but
no plan doc — that usually means the copy-bootstrap already happened but the
port itself hasn't).

Call the new step `NN_new` and the immediately preceding step `NN_prev`
throughout (e.g. `04_api_client` / `03_prompt_builder`).

### 2. Bootstrap the Python snapshot as a copy

`week1_baseline/python/<NN_new>/` must start as an **exact copy** of
`week1_baseline/python/<NN_prev>/` — nothing ported yet, just the previous
step's completed code with a new folder name. If it doesn't exist yet,
create it:

```bash
cp -r week1_baseline/python/<NN_prev> week1_baseline/python/<NN_new>
```

If it already exists (a previous session may have started this), verify it's
still an unmodified copy before touching anything:

```bash
diff -rq week1_baseline/python/<NN_prev> week1_baseline/python/<NN_new>
```

Zero diffs (other than `__pycache__`, which is `.gitignore`d) means you're
clear to proceed. Any real diff means someone already started porting this
step — read what's there before assuming you're starting fresh (see the note
on "check current state before planning" below).

### 3. Diff the two Ruby steps — this is the entire scope of the port

```bash
diff -rq week1_baseline/ruby/<NN_prev> week1_baseline/ruby/<NN_new>
```

Then `diff` (not just `diff -q`) every file that shows up as changed, to see
the exact line-level delta. This diff *is* the spec for what to port — nothing
outside it should change in the Python snapshot. Read the new step's
`README.md` in full too; it's the "source of truth" doc that explains *why*
the delta exists, not just what changed.

Watch for two common patterns that trip up the delta scope:
- A file the Ruby diff shows as "changed" that's actually just a comment or
  whitespace edit with no behavioral effect — don't port those literally if
  Python has no equivalent artifact (e.g. a stray one-word leftover comment).
- A file Ruby's diff touches that looks like a bug fix vs. one that looks like
  a bug *introduction* (e.g. a path computation that used to resolve correctly
  and now resolves to a nonexistent directory). Flag the latter explicitly in
  the plan's Design Considerations and Open Questions — don't silently
  reproduce a regression, and don't silently "fix" it either without asking.

### 4. Write the plan doc

Write `docs/plans/python_port/<NN_new>.md` using
`templates/plan-template.md` in this skill folder as the section-by-section
skeleton. Follow it closely — the heading text, table shapes, and section
order are load-bearing (later steps' plans get scanned for precedent, and
consistent structure is what makes that fast). The template has inline
`<!-- guidance -->` comments explaining what goes in each section; delete
those comments as you fill sections in, don't leave them in the final doc.

A few things the template can't fully capture, since they depend on this
step's specific delta:

- **Every non-obvious Ruby→Python translation gets its own bullet** in Design
  Considerations, even if a near-identical one appeared in an earlier plan —
  don't assume the reader has that context loaded. Common recurring ones,
  for quick reference (check the actual prior plan for the precise wording
  before reusing):
  - Ruby keyword args with a defaulted arg listed first (legal in Ruby,
    illegal in Python) → reorder Python params so defaults come last.
  - Ruby symbols (`:tokens`, `:medium`) → Python plain strings; Ruby `nil` →
    Python `None`.
  - Ruby `attr_reader`/bare method calls with optional parens → Python: pick
    `@property` vs. plain method consistently *within one class* (don't mix
    styles inside the same class just because Ruby's syntax hid the
    distinction).
  - A Ruby class-level and instance-level method sharing a name (impossible
    in Python, where the second definition just clobbers the first) → give
    one of them a different name/storage location, and say which is public.
  - Ruby's `StandardError` subclasses → Python's `Exception` subclasses
    (there's no reason to use a custom base error class unless Ruby has one).
  - A latent Ruby arity/behavior bug that's never actually exercised by the
    example → port it faithfully (matching failure mode, e.g. Ruby's
    `ArgumentError` ≈ Python's `TypeError`), and say explicitly that it's
    intentional so nobody "fixes" it in a later step by accident.
- **Open Questions are for real judgment calls, not busywork.** Only list a
  question here if Python genuinely can't do what Ruby did and someone has to
  pick a resolution — a naming collision Python can't replicate, whether to
  preserve vs. fix a Ruby-side bug, a stylistic convention that will become
  precedent for every later step. Don't pad this section; the prior plans
  average 2-3 sharp questions, not a checklist.

### 5. Get the user's sign-off on Open Questions

Show the user the plan (or at least the Open Questions section) and wait for
their answers before implementing. In this repo the user has consistently
answered tersely and directly inline under each question in the plan doc
(one line, sometimes just "do what you have to make it work" or "fix it") —
that's the expected interaction shape, not a sign they want more detail.
Treat a terse answer as a real decision and move on; don't ask for
elaboration unless the answer is genuinely ambiguous about *which* option it
picks.

If the user is mid-conversation and clearly wants to move fast (e.g. they
already dictated most of the porting decisions inline before you even
started, or previous steps in this same repo already established the
convention this question is asking about), it's fine to propose the
precedent-consistent answer yourself and flag it for a quick confirm rather
than blocking on a full round-trip — but always still surface the question,
don't silently decide.

### 6. Implement the plan

Apply only the delta:
- New files get created; carried-over files are left byte-for-byte untouched
  unless the plan's Porting Notes explicitly call out a change to them.
- Update `boukensha/__init__.py`'s exports to match the new public surface.
- Replace `README.md` and `examples/example.py` with the step's versions per
  the plan (these two always change every step, since they're the
  step-specific spec and acceptance test).
- Add `week1_baseline/bin/python/<NN_new>` — copy
  `templates/launcher.sh` from this skill folder verbatim except for the
  `<NN_new>` path, then make it executable (`chmod +x`, or on Windows Git
  Bash this repo runs on, ensure the file has the executable bit set the same
  way the existing launchers do). See "Launcher — don't skip the venv
  fallback" below; this template already has the fix baked in, so just don't
  hand-roll a different version of the launcher.

**Check current state before planning further work.** Before assuming a file
needs writing, read it — a prior session may have already implemented some or
all of the delta (this has happened in this repo: a plan was written, and by
the time implementation started the target files already matched the plan
exactly). Diff what exists against what the plan specifies; only write what's
actually missing or wrong. Don't blindly re-write files that already match.

### 7. Run the smoke test and verify

```bash
./week1_baseline/bin/python/<NN_new>
```

Check against the plan's Verification section: exit code, printed banner
line, output shape. If the step makes a real network call (anything from
`04_api_client` onward that constructs a `Client` and calls it, as opposed to
`03_prompt_builder` which only ever builds a payload dict and never sends
it), the smoke test needs a **working** API key for whichever provider
`~/.boukensha/settings.yaml` (or this repo's `.boukensha/settings.yaml`)
names in `tasks.player.provider`. A placeholder key (e.g. `"NOT_A_REAL_KEY"`
in `.boukensha/.env`) produces a real `401`/`403` `ApiError` from the live
API, not a silent success — tell the user this plainly if you hit it, and
point them at getting a real key rather than treating it as a porting bug.

## Launcher — don't skip the venv fallback

This repo's shared virtualenv lives at the repo root (`.venv`), and this repo
runs on Windows via Git Bash. `python -m venv .venv` on Windows creates
`.venv/Scripts/python.exe`, not `.venv/bin/python` — a launcher that hardcodes
only the Unix path will fail with "No such file or directory" the first time
someone runs it on Windows. This exact bug has already been hit and fixed
once in this repo (`03_prompt_builder`'s launcher was written without the
fallback and had to be patched after a live test failure) and one older
launcher (`04_api_client`) still has the un-patched, Unix-only form as of this
writing — if you're porting a step near there, or you notice a launcher
missing the fallback while you're in the area, fix it forward; it's a
one-line-diff, zero-risk correction consistent with this skill's own template.

Every launcher must look like `templates/launcher.sh` in this skill folder:
try `$repo_root/.venv/bin/python`, fall back to
`$repo_root/.venv/Scripts/python.exe` if the first isn't executable. Never
write a launcher with only one of the two paths.

## Files in this skill

- `templates/plan-template.md` — section-by-section skeleton for the plan doc
  described in step 4 above, annotated with what belongs in each section.
- `templates/launcher.sh` — the exact launcher shape described above; copy
  and adjust only the step-directory path.
