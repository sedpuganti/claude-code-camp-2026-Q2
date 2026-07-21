# what is goal for week?

We want to build a baseline agent that has all the common components for building any kind of agent. Thins it should include:
- a simple agentic loop
- a tool registry along with tools
- It should be able to handle multiple backends
- it should be able to produce logs
- it should have an DSL so we can use the agent like an SDK
- it should have global binary execution so we can interact via the CLI 
- we should have an option CLI model
- it should manage context and compact messages when reaching out set limit
- it should have its own configuration directory

Some other things we should have:
- log visualizer so we can better view the logs in our browser.

## What should the baseline be able to do?
It should be able to play the MUD though we will have to give it specific commands 

## What will not be able to do?
It will have poor perception since it doesn't have a way of managing memory, or decision making, or be token effective.

## Techinical Design Considerations
- We will use REST APIs directly, this design choice is so we are understanding how simple it is to interact with managed APIs and how much they vary.
- Some SDKS even official ones do not expose all features and so REST API will give full access to feature sets
- We are using Ruby but the end user can port it over to another language
- We must used the ruby MudManager to interact wit hthe MUD.
- We should attempt to use the Standard Library (STDs) as much as possible and avoiding introducing third party libraries.

### What should we not use?
- We should avoid using Agent SDKs since they already implement features we are implement by scratch they also might limit our ability to implement exactly what we need.
 - eg. Don't use OpenRouter, Don't use Amazon Stands or CoreAgent or LangChain
 - We shouldn't be using the Coding harness to drive the agent, since thats is not purposed for our agent task.

 ## Explain Structure Approach

 The `ruby/` folder contains each step-by-step iteration for agent.

 ### Considerations
 - We will need to make some manual adjustments since the original code didn't exist in a ruby sub-folder
 - AI affected the handwritten code and so we will idnentify parts that should be rewritten but we may leave entact not to disturb future layers
 - We can and will prot the code over to Python, we will have to ensure the MudManager ruby version works with both Ruby and Python.
 - If you 

 ## Student Completion Approaches
As a student you have some flexibility in how you can get through this week:
- You can exactly follow along and make the ruby changes.
- you can treat the ruby implemention as your main implementation
- If you have no interest in the Python porting you can completeting ignore vidoes.
- You can watch all the videos and then do a single port of the last ruby interation to your language of choice.
- YOu don't have to port the ruby but you will have to use it in your week 2 when we implement extra capabilities.


 ## Baseline Mud Agent

 The baseline mud agent is a fully working MUD agent that can connect to a tbaMUD server, log in as a character, and control it through natural language.

 **What the baseline gives you:**
 - A persistent TCP session to the MUD server that stays connected across the agent's tool calls
    - techinically the MudManager is persisting the connection
 - Five interchangeable LLM backends (Anthropic, OpenAI, Gemini, Ollama, Ollama Cloud) behind one normalized request/response shape, configured per-task in `settings.yaml`
  - Andrew implements 5 backends, the student can use a single backend or multiple backends, its up to them.
- MUD tools covering every core action: movement, combat, perception, inventory, magic, and communication
- MUDMaager implements specific actions, but there are actions missing, eg. Thief commands, rest commnads, The student needs to consider solving these at some point, In end of week 1 or in week 2.
- A standard tool library for file I/O and shell commands so the agent can also read/write local state
    - These tools are simply mirror the MudManager tools and likely need to occur in week 1.
- A multi-turn REPL so you can have a back-and-forth conversation with the agent while it plays
- Full conversation history carried across turns so the agent remembers what it has seen and done.
    - This is the sessions log files, but consider we can load previous conversations since we don't implement those features in the Agent.
- Coloured structured logging of every API call, tool dispatch, and respone
    - Techincally there is a bit of colouring, but the web-browser logger provides more information.

**what it does not yet have** (to be added in later iterations):
- Long-term memory beyond the current conversation window
- A world model or map built from exploration
- Goal planning, tactical reasoning, or autonomous behaviour
- Character progression tracking or strategy

For each of our steps ofter we will have a class for each eg. Configuration will config, REPL will have repl.rb

### 0 Configuration

`Boukensha::Config` and /.boukensha directory stores all our configuration data including Screts, prompts, logging (aka sessions) and settings file. 
We have a env var called BOUKENSHA_DIR that lets override its default location which is in the user's home directory.

We do use .dotenv standard for storing our secrets and we do need to include the dotenv library
> why configuration directory? If we are building an agen that can be deploy on multiple servers a configuration directory seem appropriate.

- the single source of truth for all settings. Loads `~/.boukensha/` by default (override with `BOUKENSHA_DIR`). Reads `.env` for secrets, `settings.yaml` for options, and `system.md` for the default system prompt.

### 1 The Struct Skeleton

Define `Boukensha::Tool`, `Boukensha::Message`, and `Boukensha::Context` as plain data containers. No logic yet, just the shapes.

We are defining the main datastructure to pass around the data.

### 2 The Tool Registry

`Boukensha.tool` DSL method that registers a name + block. Add `Boukensha.dispatch(name, args)` to call one. Runnable: register a fake tool and call it.

The tool registry is reponsible for managing a data table of possible tools, and also dispatch tools when called. In other words itmatches a prompt call to an appropriate tool.

> we did discover that the at somepoint the AI regressed the implementation and Context is still responsible for managing tools which is not correct and the tools[] need to be moved to the Tool Registry

### 3 The Prompt Builder

Since we are calling muliple backends via direct REST API requests, we need to know exatly their schema structure, So we need to build those expected structures.

We also need the prompt builder to normalize the responses into a single standard.

`Context#to_messages` that serializes history into the Anthropic messages array format. Runnable: print the assembled prompt to stdout
> We have to consider the thinking option models, some models have thinking turn on default where others do not, some cannot turn off thinking. There are other parameters we can fine tune, but we didn't much time exploringthem in the video.

### 4 The API Client

The API Client is simply a low-level http-sever making a direct API call to the REST API.

> We end up hardcoding the exact OpenSSL path, and this changes based on Windows, Mac or Linux, a third party http-server like HTTPParty or Faraday would solve this but it will abstact more and make it harder to see the moving parts and we would have to take a library so we just fix the code for where we run it.

A thin `Boukensha::Client` that wraps a single POST `/v1/messages` call. No tool loop yet, just one round-trip. Runnable: send a plain message, print the response. Also lands the `Backends::*` / `Tasks::*` split - provider and model come from `tasks.player.*` in `settings.yaml` rather than being hardcoded, and each backend owns its own supported-model table (context window, cost metadata).



### 5 The Agent Loop

`Boukensha::Agent` - the core agentic loop. Calls the API, checks `stop_reason`, dispatches tool calls back into the registry, appends results to the context, and repeats until `end_turn` or `MAX_ITERATIONS` is hit. Adds `Boukensha::Erros` (`LoopError`, `ApiError`) and wires everything together in `Boukensha.run`. Also brings the OpenAI, Gemini, and Ollama Cloud backends online alongside Anthropic and Ollama - each implements `parse_response` to convert

> So we mentioned earlier we need to normalize the responses in the prompt backend and so it occurs here I believe we implement that normalization within the prompt builder and their backends.

### 6 The Logger

We creae a logger which will record the logs of a sessin in `/.boukensha/sessions/
<date>-<session_id>.json

> We have a log_viz app which is a simple sintra app to visualize the sessions, we should really in the future port it to typescript and have it realtime.

We make sure we store exactly which model, which provder and cost, trying up uplift as much information on each call for details reporting and also allowing us to mid conversation switch agents (despite lacking commands to due so in the CLI)

`Boukensha::Logger` - structured, coloured terminal output for every phase of the agent loop (iteration header, prompt dump, tool call, tool result, response). Supports an optional JSON log fine (`log:` path). Respects `Boukesha.quiet!` / `Boukensha.loud!` to suppress terminal output without stopping file logging. `Boukensha.debug!` enables raw API response logging.

### 7 The Run DSL

Up to this point we have multiple classes we need to create instances of and it becomes a mess of code so we implement a single .run command to abstract away the complexity and give us a SDK like interface to our agent.

`Boukensha::RunDSL` - the object `self` becomes inside a `Boukensha.run {}` block. Exposes a single `tool` method so callers can register ad-hoc tools inline alongside the task, keeping the DSL surface small and the main `Boukensha.run` signature clean.

### 8 The REFL Loop

It lets us have interactive loop for the terminal
 `Boukensha::Repl` - an interactive session that stays alive across turns. Reads user input, runs the agent, prints the reply, and loops back to the prompt. A single `Context` is shared acorss all turns so the agent sees full conversation history. Build-in commands: `/quiet`, `/loud`, `/clear` (wipe history, keep tools), `/exit` / `/quit`, `/help`. Adds `Boukensha::VERSION` 

 ### 9 Global Executable

 lets us called `Boukensha` anywhere in the terminal to start using our agent.

 > Here we a .boukensharc get interduce which allows use to set the configuration path and the current gem path for boukensha binary to load and we end up having to carry that code in future steps

 Packages everything as an installable gem so the `boukensha` commnad is available anywhere on the machine. Adds `boukensha.gemspec`, `bin/boukensha`, and `lib/boukensha_loader.rb`, The loader resolves which step folder to use in priority order: `BOUKENSHA_PATH` env var -> `~/.boukensharc` file -> bundled default. `BOUKENSHA_DEBUG=1` prints the resolved path on startup.

 --sh
 cd 09_global_excecutable
 gem build boukensha.gemspec
 gem install boukensha-0.9.0.gem
 BOUKENSHA_PAHT=~/Sites/boukensha/09_global_executable boukensha
 ...

 Each step from here on ships its own gem the same way (`gem build boukensha.gemspec && gem install boukensha-<version>.gem`) - point `BOUKENSHA_PATH` at whichever step folder you want to run.

 > we skip this step for Python port, Not sure if that was a bad idea but we do that.

 ### 10 Standard Tool Library - MCP Host

 We are implementing a mapping of tools for the agen from the Mud Manager.
 However when we went to port the code to python the python app had no way of accessing the MudManager ruby version so we end up implementing MCP

 > The MCP implementation is a 2 hour video and its worth watching but not doing, so I would recommond copying over the MundManager and the 10_standard_tool_library from omeking repo.

 > we end up adding the MCP server within Mud Manager so its single gem.

 > Also due the major code changes we end up having to carry forward code which makes the ruby step more involved.

 This step originally shipped there build-in tool modules (`Tools::FilesSystem`, `Tools::Shell`,`Tools::Mud`). That code has since been **deleted and replaced** by an MCP-host rewrite that also applies to every step after this one - the directory keeps its `10_standard_tool_library` name only so step ordering and existing paths still resolve.

 Boukensha now ships **no tools of its own**. It is an MCP *host*: every tool the agent can call comes from an MCP server declared in `settings.yaml`. An agent with an empty `mcp_servers:` block can only talk.

 **`Boukensha::Mcp::Client`** - a minimal MCP-over-stdio client: spawn a server, handshake, `tools/list`, `tools/call`. Server-agnostic; `command` / `args` / `env` is the stardard stdio transport config.
 - **`Boukensha::Tools::Mcp`** - the only file left under `tools/`. Registers a server's discovered tools into the registry, optionally scoping their names with a `prefix:` (client-side only - a collision between two server's tool raises rather silently clobbering).
 --**`mcp_servers:` in `settings.yaml` ** - adding a capability is a config edit, not a code change. Each entry takes `command`,`args`, `env`, `prefix`, and `required: false` (downgrade a failed start to a warning instead of an error).
-File access and shell commands now come from whichever filesystem/shell MCP server you plug in. MUD gameplay comes from the `mud-manager --mcp` daemon (the same `mud_manager` gem the old `Tools::Mud` wrapped, now run as a seperate process).
- `working_dir:` survives on `Boukensha.run` / `.repl` but is now Context metadata only - it register nothing.

### 11 Terminal UI

TUI is just a nicer REPL, so it has advanced display features within terminal

> we use Charm's BubbleTea for the TUI in Ruby, AI thinks bubble Tea is not available for python and so ends up using Texual. In honestly we have the log_viz we don't really need a TUI but in my original implementation I implemented log_viz later.

Adds a full terminal UI (TUI) on top of the MCP-host tool model, built on the [`charm`] (https://github.com/charm-ruby/charm) gem (bubbletea _ + lipgloss + bubbles). The plain REPL is still there via `tui: false`.

- ** `Boukensha::Tui`** - wraps a `Repl` and replaces raw `puts`/`gets` with a four-zone display: scrollable conversation viewport, a live progress line (spinner, iteration counter, elapsed time, token counts, tool call count), an input box, and an always-on status line (version, model, context tokens used/max, tool count, wall-clock time). The agent runs on a backgroud thread so the UI stays responsive during a turn.
- keyboard shortcuts: `Enter` submit, `Esc` interrupt the running turn, `Ctrl+L` clear history, `PgUp`/`PgOn` scroll, `Ctrl+C`/`Ctrl+D` quit.
- ** `Boukensha.repl(tui:)` ** = `true` (default) launches the charm TUI, `false` falls back to plain REPL. `--no-tui` sets this form the command line.
- **`Repl` referenced for composability** - no longer hard-codes I/O. `on_output(&block)`, `handle_command(input)`, and `run_turn(input)` are public so any front-end can drive it. 
- **`Logger#subscribe`** - every structured log event is now broadcast to subscribers in addition to being written to the JSONL file, which is how `Tui` updates its progress line in real time without pooling.

### 12 Context Management

There is no auto-compacting when you call an LLM directly - you're responsible for the context window. This step addes proper token tracking, visual warnings, and automatic compaction on top of the MCP-host tool model and TUI carried forward from steps 10-11.

> There should be settings exposed to increase the 600 eg. 60,000 max token 

-**Acurate token tracking** - `Context` now tracks `context_window` (the model's max input capacity, from `Boukensha::Models.context_window(model)`) separately from `current_tokens` (actual usage from the most recent API response), fixing an earlier display that conflated the output-token budget with the context window and let a commulative session sum grow unbounded pas `/clear`.
- **`Boukensha::Models`** - a static model -> capablity table built from backend's own model list, so `Context` can be sized correctly before a backend is contructed. Unknown models fall back to a conservative default rather than assuming a huge window.
-**Colour-coded context indiacator** - grey under 70% used, yellow 70-84%, red (with a `delta`) at 85%+ , shown in both the progress and status lines.
--** 