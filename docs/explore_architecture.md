# Explore Agent Architectures

The largest confusion tech professionals have is applying the correct agent solution because many solutions appears to overlap responsibilities.

We will explore multiple agent architechture to determine fit for our agent workload.

## 1. An agent file with referenced files eg. AGENT.md,   @~/docs/*.MD

The simplest agent is creating an "agent file" and possibly importing other files that are read conditionally when needed.

We should attempt to create an agent file and see if it can connect to the MUD and complete a simple goal:
eg. "Find the bakery and list the menu."

We want to use the smallest and least intelligent model and scale up.

### Techincal Observations

Using Haiku 4.5 we created a CLAUDE.md with simple prompt, and told it will need to manage its own local memory via simple markdown files. We provided it with the location of the MUD and the players credentials.

The agent struggled to connect to the MUD.
The agent would attempt to create temporary code files to manage a telnet connection and execute commands.
The agent did not have enough information about Text User Interface of the MUD to login and see its mistake.