---
name: play-mud
description: Connect to tbaMUD on localhost:4000, execute commands, and maintain persistent memory for long-term goals
license: MIT
compatibility: opencode
---

## Overview
Connect to tbaMUD (CircleMUD) on localhost:4000 as player `dummy` / `helloworld` and drive toward long-term goals using persistent memory files.

## Quick Commands
```bash
# Run a command (auto-login, fresh connection each time)
python3 scripts/mud.py "<command>"
python3 scripts/mud.py "cmd1;cmd2;cmd3"
python3 scripts/mud.py "cmd1;cmd2" --wait 2.0

# With persistent memory (auto-loads/saves player.md and world.md)
python3 scripts/mud.py "score;look;eq" --data-dir ./data
```

## Memory System (data/player.md + data/world.md)
The `--data-dir ./data` flag enables persistent memory:
- **Before** execution: loads existing state from `data/player.md` and `data/world.md`
- **After** execution: auto-updates stats from `score` output and merges every room seen
  into `data/world.md`'s "Explored Rooms" catalog (keyed by room name — it accumulates
  across runs rather than overwriting, so the map only grows)
- Also saves `last_output.txt` for debugging

### Goal structure (data/player.md `## Goals`)
Goals are tracked as a checklist so progress persists across many separate invocations:
```markdown
## Goals
### Primary Goal
- Reach level: 7
- Defeat: <monster name>

### Sub-goals
- [ ] Get basic weapon and armor
- [ ] Find and join a guild, learn combat skills
- [ ] ...

### Attempts & Notes
- log what worked / didn't work here
```
Check off `[x]` sub-goals as they're completed, add new ones as they're discovered, and
keep the Attempts & Notes log current — that's what lets a later session (with no memory
of this one) pick up where it left off instead of re-discovering the same dead ends.

### How to use memory for long-term goals
1. Run `python3 scripts/mud.py "score;look;eq" --data-dir ./data` to start
2. After every action, **update the memory files yourself**:
   - `data/player.md` — check off/add sub-goals, track equipment, inventory, learned
     spells/skills, faction standings, and notes about what you've tried
   - `data/world.md` — the "Explored Rooms" section auto-fills itself; add manual notes
     above/below it for things `look` doesn't capture (shop menus, quest givers, routes)
3. Before complex actions, check your goals in `data/player.md` and plan sub-goals
4. Reflect on what worked/didn't work and update notes

## Example workflow for reaching level 7
```
# 1. Check status and surroundings
python3 scripts/mud.py "score;look;eq;inv" --data-dir ./data
# Update data/player.md: check/add sub-goals (get weapon, train, find hunting spot)

# 2. Explore toward hunting grounds -- world.md accumulates rooms automatically
python3 scripts/mud.py "s;s;e;look" --data-dir ./data

# 3. Fight and grind
python3 scripts/mud.py "kill mob" --data-dir ./data
python3 scripts/mud.py "get all;score" --data-dir ./data
# Update data/player.md: track XP, loot, HP/Mana after fight, log what worked

# 4. Repeat until level 7, then pursue the specific monster
```

### Automated grinding (scripts/grind.py)
For repetitive "level up, then hunt the target monster" loops, `grind.py` drives
`mud.py` on its own: it reads the target level/monster straight out of
`data/player.md`'s Goals section (or take CLI overrides), detects mobs and exits by
parsing live `look` output each step rather than assuming any fixed room names, and
refuses to attack known town fixtures (guards, shopkeepers) since that gets you jailed
or killed instead of earning XP.
```bash
python3 scripts/grind.py                          # reads goals from player.md
python3 scripts/grind.py --target-level 7
python3 scripts/grind.py --target-monster minotaur
```
It's heuristic — mob-keyword guessing and DFS-style exploration aren't perfect — so
check in on `data/player.md`'s Attempts & Notes and `data/world.md` afterward and
correct course by hand if it gets stuck.

## Notes
- Logs in as `dummy` / `helloworld`
- Recovers from sleep/rest on login
- Strips ANSI codes and telnet control sequences from output
- Each invocation is a fresh connection
- Auto-parses `score` → `data/player.md`; auto-merges every room from `look` → `data/world.md`
- Agent should manually maintain Goals (checklist), Equipment, Inventory, and strategy notes
