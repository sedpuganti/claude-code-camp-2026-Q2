# 01 · Struct Skeleton (Python port)

We want to able to manage all configurations from an external file eg. `~/.boukensha/settings.yaml`
We want a dedicated class to handle configuration. eg. `boukensha.Config`
Please consider that as we add configuration in each iteration we will be updating the configuration schema and class.
We can hardcode defaults but we should not hardcode configurable values.

Configuration is organised by **task** — a role in the agentic loop bound to its
own LLM. week1_baseline only drives a single `player` task (the main loop), but
a more advanced loop will assign different LLMs to different tasks. A task is
either a "single-task" or a "multi-task" — the latter being a full agent.

This is the Step 1 snapshot. It retains the Step 0 configuration behaviour and
adds the lightweight Tool, Message, and Context structures from
`week1_baseline/ruby/01_struct_skeleton`.

## Setup

All Python steps in this repo share a single virtualenv at the **repo root**,
so it only needs to be created once. From the repo root:

```bash
python -m venv .venv
```

Activate it (pick the one matching your shell):

```bash
source .venv/bin/activate        # macOS/Linux, Git Bash on Windows
.venv\Scripts\activate.bat       # Windows cmd.exe
.venv\Scripts\Activate.ps1       # Windows PowerShell
```

Then install this step's dependencies:

```bash
pip install -r week1_baseline/python/01_struct_skeleton/requirements.txt
```

Later steps will add their own `requirements.txt` — re-run `pip install -r
<step>/requirements.txt` against this same `.venv` after activating it.

## Design Considerations

We want to use the standard library as much as possible, avoiding external
packages. Two are unavoidable here:

- `PyYAML` — Python's stdlib has no YAML parser, playing the same role as
  Ruby's built-in `yaml`.
- `python-dotenv` — direct equivalent of Ruby's `dotenv` gem, for loading
  `.boukensha/.env`.

## Code Changes

| File | Purpose |
|------|---------|
| `boukensha/config.py` | `Config` class |
| `boukensha/tasks/base.py` | abstract `Base` (provider/model + prompt resolution) |
| `boukensha/tasks/player.py` | concrete `Player` (the main loop) |
| `boukensha/tool.py` | registered agent capability and its callable handler |
| `boukensha/message.py` | one conversation entry |
| `boukensha/context.py` | system prompt, messages, and registered tools for a task |
| `boukensha/__init__.py` | top-level package exports |
| `prompts/system.md` | default system prompt shipped with the library |
| `examples/example.py` | runnable smoke-test |

---

## Struct Skeleton

`Tool` describes a capability available to the agent. It stores its name,
agent-facing description, parameter schema, and Python handler. Registering a
tool does not invoke it yet.

`Message` stores a `role`, `content`, and optional `tool_use_id`. The latter
will later link a tool result to the exact tool request that caused it.

`Context` owns all state that will be sent to a future API call: the task
class, system prompt, conversation history, and registered tools.

```python
from boukensha import Context, Tool
from boukensha.tasks import Player

ctx = Context(task=Player, system="You are a MUD player assistant.")
ctx.register_tool(
    Tool(
        "look",
        "Look around the current room",
        {},
        lambda: "You see a torch-lit corridor.",
    )
)
ctx.add_message("user", "Look around.")
```

At this step, `Context` only holds state. Tool execution, API requests,
message serialization, and token budgeting arrive in later snapshots.

---

## Config directory resolution

The class looks for a `.boukensha/` directory in this order:

1. **`BOUKENSHA_DIR` env var** — set this to point at any directory you like.
2. **`~/.boukensha`** — the default location for a real install.

## Config directory structure

The class expects the following:

```
.boukensha/
  .env                 # stores credentials eg. LLMs APIs (never committed to repo)
  settings.yaml        # all non-secret settings
  prompts/
    <task>/
      system.md        # per-task override for the default system prompt (optional)
```

---

## Tasks

`boukensha.tasks.Base` is an abstract stateless class. All behaviour is
expressed as classmethods that accept a `settings` dict — no instances are
created. Concrete subclasses define `task_name()`. For now only
`boukensha.tasks.Player` exists; future steps add per-turn ceilings
(`max_iterations`, `max_turn_tokens`, `max_output_tokens`,
`compaction_threshold`) — these are **not** read yet.

`Config.tasks()` returns the raw dict from `settings.yaml` under `tasks:`.
Pass a name to look up a specific task's settings dict, then pass it to the
stateless class:

```python
Player.provider(config.tasks("player"))
Player.system_prompt(
    config.tasks("player"),
    user_prompts_dir=config.user_prompts_dir(),
    default_prompts_dir=Config.PROMPTS_DIR,
)
```

## System prompt resolution

Per task, `Player.system_prompt` is resolved in this order:

1. **`.boukensha/prompts/<task>/system.md`** — used when the task's
   `prompt_override.system` is `true` and the file exists.
2. **`prompts/system.md`** — the default system prompt shipped with the library.

(We no longer use a top-level `system.override`; override is now per-task via
`prompt_override.system`.)

## Configuration Schema

The following properties so far:
- `tasks`: a map of task name → task config (provider, model, prompt_override).
- `tasks.<name>.prompt_override.system`: when `true`, the task's
  `.boukensha/prompts/<name>/system.md` overrides the default system prompt.
- `mud`: MUD connection information for the main player.

```yaml
tasks:
  player:
    provider: anthropic        # provider name (string)
    model: claude-haiku-4-5
    prompt_override:
      system: true
mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

## Run Example

```bash
./week1_baseline/bin/python/01_struct_skeleton
```

Expected output (values from your `.boukensha/`):

```
=== Boukensha Step 1: Struct Skeleton ===

Config:   #<Boukensha::Config dir=/.../.boukensha tasks=player>
Context:  #<Context task=player turns=2 tools=1>
Tool:     #<Tool name=move description=Move the player in a direction (north, so params=['direction']>
Messages:
  #<Message role=user content=Explore north and tell me what you find....>
  #<Message role=assistant content=Sure, let me head north and take a look....>
```

## Considerations
These are things we observed but we do not want fixed since future steps will break.
- We have default prompt eg. prompts/system.md it supposed to be scoped on task eg. prompts/
<task>/system.md
- Our settings file should accept .yml or .yaml, right not it only takes .yaml
- `prompt_override?` had no direct Python equivalent — ported as
  `is_prompt_override` (explicit boolean-returning-method convention), to be
  applied consistently in later ports.
