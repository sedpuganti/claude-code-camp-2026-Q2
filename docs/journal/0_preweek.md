# Technical Journaling Format

In this bootcamp you are expected to produce technical documentation.
This is help to document gained technical domain knowledge.

Please use the following format.

## Technical Goal
The technical goal of of preweek (Explore) is to determine how well do Agent Architectures fit our business use-case.

Examples of Agent Architectures That Scale with Effort:

- An agent file with referenced files eg. AGENT.md, ~/docs/*.MD
- Agent Skills driven by main agent eg. ~/.skills
- Filesystem Subagent driven by a coding harness or Coding agent SDK eg. ~/subagents
- AI workflow automation platform eg. n8n
- Use a generic AI Agent SDK that leverages plug and plays and plays genaric AI packages.
- Use low level first-party LLM SDKs and write our own agentic loop
- Use REST APIs directly, write our own agentic loop
    - The agentic loop is model-driven orchestration with middleware programmatic guidance
    - The agentic loop is code-driven orchestration


## Technical Uncertainty

- I'm uncertain if an coding harnesses agentic loop is effective/productive enough to drive a non-coding workload.
- I'm uncertain if LLMs model's thinking model and other intelligent parameters is sufficent enough to hold memory and drive decisions for work specific use-case.
- I'm uncertain that a coding harnesses can interact with a MUD without an interface or SDK or manage the telnet session.

The goal to reach level 7 and defeat the minotaur remains blocked by the MUD's combat mechanics not functioning properly for this character.

## Techinical Hypotheses
- Based on our [Ref 1] i think that we will have issues with the coding harness driveing the MUD without an interface because we don't a defined API, we are driving commnads over a protocol that we need to live-monitor. Telnet communincation seems like it would be a sticking point.

- I think we will need an interface because managing a long-lived telnet session may prove difficult. In that pass I've always found manging live-sessions challenging.

- I think that only agent architecture that will be able to drive over use-case will be where we implement a specialized agentic loop, as i think generic models memory will not be capable enough to remember and navigate the MUD world.

- I think that we need to roll-our-own agent without an SDK because generic primitives for observability, for memory, and our use-case will required specialized implementation. And that we want to connect broadly will all forntier models and many SDKS will lack one of them.

## Technical Observations

Here are the things I found out while doing the experiments.

For the first approach using AGENT.md files, the agent was able to connect to the game which is good. But every time you give it a new task, it would create new code from scratch just to handle the telnet connection. It doesn't realize that it can just reuse the previous code. It also has no memory, so if you told it something before, it would forget on the next task. Simple things like looking around and moving worked fine, but when you give it something complicated like defeat the minotaur, it doesn't know where to start.

For the second approach using Skills, this one was better because the MUD connection code and common commands are already there in the skill file. The agent doesn't need to recreate everything each time. But even with this, the agent still had a hard time with planning. When we said defeat the minotaur, instead of thinking that it needs to level up first and get some equipment, it went straight to looking for the boss room. It was only level 1, so it couldn't win. It also couldn't open locked doors, so it got stuck in certain areas.

Other things I discovered along the way. The path from the temple in Midgaard to the newbie zone entrance is four steps north then one step east. The minotaur which is mob number 18609 is in room 18629 called The Red Room on the lower level of the newbie zone. Its stats are level 7, 1000 to 3000 HP, armor class 15, and damage of 3d5+85 which is around 88 to 100 per hit. To have a chance against it, you need to be at least level 6. That means a lot of grinding, killing newbie monsters, dragons, and zombies. The mud.py script works fine but it creates a new connection every time you call it which takes about 10 seconds. The telnet negotiation really needs to be handled properly especially the terminal type and echo codes or the connection will hang.

Here are the key files I used this week and what they are for:

The **`01_plain_agent/AGENTS.md`** is the prompt for the first experiment. It tells the agent to just use telnet or nc to connect and manage its own memory through markdown files. What happened was the agent kept trying to generate its own telnet code every session instead of reusing the connection. Such a waste of tokens.

The **`02_agent_skills/.claude/skills/play-mud/SKILL.md`** is the skill definition for the second approach. It wraps the mud.py script as a reusable skill so the agent does not have to keep recreating the connection logic. It also documents the `--data-dir` memory system for tracking the player stats and world state across sessions.

The **`02_agent_skills/.claude/skills/play-mud/scripts/mud.py`** is the main MUD client. It handles connecting to the game at localhost:4000, logging in as dummy/helloworld, stripping those ANSI color codes, and running commands separated by semicolons. But each call opens a fresh TCP connection so there is about 10 seconds of overhead from all the login delays.

The **`02_agent_skills/.claude/skills/play-mud/scripts/grind.py`** is the automation script I wrote to call mud.py in a loop. It tries to navigate to the newbie zone, find monsters, kill them and level up. It struggled though because the character position persists between sessions and does not always start at the temple.






## Technical Conclusions

Below is the summary of what's completed and pending.

play-mud Skill Development & Testing
- ✅ Fixed socket timeout issues in mud.py (improved _recv buffering, telnet IAC filtering)
- ✅ Resolved login authentication (character name confirmation, proper credential handling)
- ✅ Implemented goal-driven memory system (player.md, world.md accumulation)
- ✅ Rewrote grind.py for dynamic mob detection and DFS exploration
- ❌ Goal not completed: Combat system appears non-functional (kill commands don't award XP)

Final State:
- Character: dummy (Level 1, 2/2500 XP)
- Connection: Stable
- Skills: Working (login, navigation, status checks)
- Blocker: Combat/XP mechanics need debugging or different approach

The skill infrastructure is solid—infrastructure for long-term goal tracking and automated grinding is in place. The remaining issue is the MUD's combat system not rewarding XP despite successful mob encounters.

After testing both approaches, I think both can connect to the game and do basic commands. But they are not enough for something like the minotaur quest where you need multiple steps. The thing is, the agents do not really know how to break down a big goal into smaller ones. Instead of thinking that they need to level up first, explore the lower level, and then fight the boss, they just go straight for the end goal. That approach will not work, sadly.

The markdown memory system works for small things, but if the world gets bigger you will need something like a database or vector store. The grind.py script automates the leveling loop by calling mud.py repeatedly, and it got us as far as navigating to the hunting area. After mapping out the full route and the minotaur's stats from the world files, we know the strategy even if we haven't executed the final kill yet.

For the next steps, I think we need to build a custom agentic loop. One that has proper planning, different modes for risk and exploration, and real-time visibility so you can actually see what the agent is thinking while it works. Not just a black box where you have no idea what is happening inside.


## Key Takeaway

The off-the-shelf agent loops, they are not really made for complex goals. They lack planning and they lack persistence. If we want to actually finish something properly, you really need to build your own loop with proper goal decomposition, behavioral modes, and state management.
