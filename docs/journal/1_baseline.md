# Technical Journaling Format


## Technical Goal


- is to learn how to build the AI agents that will work based on task/ some input and works toward a goal

- Learned how to build the Agent step by step including configuration, prompt building, api communication, agentic loop. session logging, mcp integration, repl, TUI, and context management. 
-  Port the boukensha implementation from Ruby to Python.
- Verify step by step by running the examples and issues the commands and checking the logs (in browser) that are stored in the sessions. 
example commands: 
1. finding the player location
2. Bekery location and it's Menu.
3. where am i currently.
- Navigate the MUD and complete the game goals.

- Understand how boukensha communicates with external tools through MCP servers such as mud-manager and filesystem server.



## Technical Uncertainty

- Initially, I was uncertain about which LLM provider and model to use. I experimented with different models to balance capability, cost, and token usage.

- I was uncertain why Boukensha sometimes started without tools or remained idle after receiving a request.
- I also encountered uncertainty around Windows compatibility, especially virtual-environment paths, Ruby native extensions, Go dependencies, executable resolution, and terminal UI behavior. It was initially unclear which component was responsible for maintaining the MUD connection and player state etc.

## Techinical Hypotheses
- When a user submits a goal, the agent enters an agentic loop that repeatedly evaluates the current context, selects an MCP tool, observes the result, and decides what to do next.

- Boukensha itself does not need built-in knowledge of the MUD. It can discover and use the tools exposed by the mud-manager  MCP server.

- An empty MCP tool registry would allow the agent to communicate with the LLM but would prevent it from observing or interacting with the game.

- If tbamud__look is not called, the agent cannot observe the current room and therefore cannot navigate reliably.
- Individual LLM API calls are stateless, but the application is stateful overall. Boukensha preserves conversation context, while mud-manager maintains the active MUD session and player connection.

## Technical Observations
- Initially, mud-manager appeared to start correctly, but Boukensha remained idle or could not locate the player or bakery.
- I observed that the expected tbamud look tool was not being called. Further investigation showed problems involving MCP startup, tool discovery, Windows command resolution, and server-response handling.

- Boukensha is an MCP host. Its available tools come from the mcp_servers section of settings.yaml.
- The LLM does not invoke MCP servers directly. It returns a tool-use request, Boukensha executes that request through its MCP client, and the result is added to the next LLM request.

- mud-manager provides a language-independent MCP interface around the MUD. This allows Ruby, Python, Java to use the same MUD tools.

- The agentic loop continues until the model produces a final response or reaches max iterations or max token usage. 

- Session logs are written Sessions directory. These logs make it possible to review tool calls, responses, token usage, and errors. 

- Architecture and MUD maps helped me understand both the command flow and the relationships between game rooms.

## Technical Conclusions

- I have complted the week 1 implementaion steps and exceuted the associated plans.
- Verified the implementations through example launchers, MCP tool discover, MUD commands and session logs.
- Flow: User goal -> bokensha repl or TUI -> Agentic loop -> LLM API requst -> MCP Client -> mud-manager or Filesysem server -> tool result/findings to bokensha.

- My next goal is to perform additional experiments and port the same architecture to Java(which is i'm more comfortable using).



## Key Takeaway
- The main takeaway is that an AI agent is more than a single LLM API call. A useful agent combines prompts, conversation  context, an iterative decision loop, external tools, persistent application state, logging, error handling, and clearstopping conditions.

-  MCP separates the agent from tool-specific implementations. Boukensha does not need to understand how a MUD or filesystem works internally; it only needs to discover and call the tools exposed by their MCP servers. This makes the architecture reusable across Ruby, Python, Java etc.