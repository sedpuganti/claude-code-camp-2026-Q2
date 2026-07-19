#!/usr/bin/env python3
"""
Goal-driven grinding bot for play-mud.

Drives toward the goals recorded in data/player.md: reach a target level,
then hunt down and defeat a named monster. Unlike a scripted route, this
discovers mobs and exits by parsing live `look` output each step -- it
doesn't assume any specific room names or mob names, since those vary by
what's actually been explored (check data/world.md for the accumulated map).

Usage:
  python3 grind.py                          # reads target level/monster from player.md
  python3 grind.py --target-level 7
  python3 grind.py --target-monster minotaur
  python3 grind.py --data-dir ./data
"""

import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from mud import parse_room_from_output  # noqa: E402

MUD_PY = os.path.join(os.path.dirname(__file__), "mud.py")
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

MOVE_DIRS = ["n", "s", "e", "w", "u", "d"]
OPPOSITE = {"n": "s", "s": "n", "e": "w", "w": "e", "u": "d", "d": "u"}

# Words to ignore when guessing a mob's `kill` keyword from its room-description line.
STOPWORDS = {
    "a", "an", "the", "is", "are", "here", "there", "standing", "stands",
    "walking", "around", "cleaning", "up", "guarding", "entrance", "looking",
    "for", "food", "mucking", "through", "garbage", "cuddling", "something",
    "furry", "hands", "and", "in", "on", "at", "with", "of", "his", "her",
    "its", "impatient", "look", "face", "counter", "slightly", "installed",
    "wall",
}

# Known town fixtures / authority NPCs -- attacking these gets you jailed or killed,
# not XP, so grind.py refuses to target anything matching these words.
SAFE_NPCS = {
    "cityguard", "guard", "guards", "weaponsmith", "grocer", "knight",
    "templar", "janitor", "baker", "shopkeeper", "receptionist",
    "immortal", "wizard", "teller", "machine", "peacekeeper", "shop",
}

FAIL_PHRASES = ("isn't here", "don't see", "kill who", "huh", "nothing by that name")


def run(cmds, data_dir, wait=None, timeout=30):
    args = [sys.executable, MUD_PY, cmds, "--data-dir", data_dir]
    if wait:
        args += ["--wait", str(wait)]
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.stdout


def parse_stats(output):
    stats = {"hp": 0, "max_hp": 0, "mv": 0, "max_mv": 0, "xp": 0, "xp_next": 0, "level": 1}
    for line in output.split("\n"):
        m = re.match(r"You have (\d+)\((\d+)\) hit.*?and (\d+)\((\d+)\) movement", line)
        if m:
            stats["hp"], stats["max_hp"] = int(m.group(1)), int(m.group(2))
            stats["mv"], stats["max_mv"] = int(m.group(3)), int(m.group(4))
        m = re.match(r"You have (\d+) exp", line)
        if m:
            stats["xp"] = int(m.group(1))
        m = re.match(r"You need (\d+) exp to reach your next level", line)
        if m:
            stats["xp_next"] = int(m.group(1))
        m = re.match(r"This ranks you as .+ \(level (\d+)\)", line)
        if m:
            stats["level"] = int(m.group(1))
    return stats


def parse_last_room(output):
    """Return (name, exits_line, entity_lines) for the LAST room seen in a multi-command run."""
    for block in reversed(output.split("\n---\n")):
        name, _desc, exits_line, entities = parse_room_from_output(block)
        if name:
            return name, exits_line, entities
    return "", "", []


def exit_dirs(exits_line):
    m = re.search(r"Exits:\s*([a-zA-Z ]+)", exits_line)
    if not m:
        return []
    return [d for d in m.group(1).split() if d in MOVE_DIRS]


def is_safe_npc(entity_line):
    low = entity_line.lower()
    return any(kw in low for kw in SAFE_NPCS)


def mob_candidates(entity_lines):
    """Best-guess `kill` keywords per hostile-looking entity line, longest word first
    (longer words tend to be the actual mob noun rather than filler)."""
    candidates = []
    for line in entity_lines:
        if is_safe_npc(line):
            continue
        words = re.findall(r"[A-Za-z']+", line.lower())
        words = sorted({w for w in words if w not in STOPWORDS and len(w) > 2}, key=len, reverse=True)
        if words:
            candidates.append(words)
    return candidates


def try_kill(data_dir, entity_lines):
    """Attempt to fight something in the room. Returns (fought, combat_output)."""
    for words in mob_candidates(entity_lines):
        for word in words:
            out = run(f"kill {word}", data_dir, wait=2.5)
            low = out.lower()
            if any(p in low for p in FAIL_PHRASES):
                continue
            return True, out
    return False, ""


def is_low_hp(stats):
    return stats["max_hp"] and stats["hp"] < stats["max_hp"] * 0.4


def is_winded(stats):
    return stats["max_mv"] and stats["mv"] < stats["max_mv"] * 0.15


def rest_until_ready(data_dir):
    for _ in range(6):
        out = run("rest", data_dir, wait=2.0)
        stats = parse_stats(out)
        if not is_low_hp(stats) and not is_winded(stats):
            break
    run("stand", data_dir, wait=1.0)


def read_goals(data_dir):
    """Pull target level / monster out of data/player.md's Goals section, if set."""
    path = os.path.join(data_dir, "player.md")
    target_level, target_monster = None, None
    if os.path.exists(path):
        text = open(path).read()
        m = re.search(r"[Rr]each level[: ]+(\d+)", text)
        if m:
            target_level = int(m.group(1))
        m = re.search(r"[Dd]efeat(?: monster)?:\s*(.+)", text)
        if m:
            name = m.group(1).strip().strip("-").strip()
            if name and "<" not in name and "fill in" not in name.lower():
                target_monster = name
    return target_level, target_monster


def explore_step(data_dir, visited):
    """Step toward an unvisited exit from the current room; backtracks dead ends.
    Returns (name, exits_line, entity_lines) for wherever it ends up."""
    out = run("look", data_dir, wait=1.0)
    name, exits_line, entities = parse_last_room(out)
    if not name:
        return "", "", []
    visited.add(name)

    for d in exit_dirs(exits_line):
        moved = run(f"{d};look", data_dir, wait=1.0)
        new_name, new_exits, new_entities = parse_last_room(moved)
        if new_name and new_name not in visited:
            return new_name, new_exits, new_entities
        back = OPPOSITE.get(d)
        if back:
            run(back, data_dir, wait=1.0)

    return name, exits_line, entities  # nothing new adjacent


def hunt_for_level(data_dir, target_level):
    print(f"=== Hunting toward level {target_level} ===")
    visited = set()

    while True:
        stats = parse_stats(run("score", data_dir, wait=1.0))
        print(f"  L{stats['level']} XP:{stats['xp']}/{stats['xp'] + stats['xp_next']} "
              f"HP:{stats['hp']}/{stats['max_hp']} MV:{stats['mv']}/{stats['max_mv']}")

        if stats["level"] >= target_level:
            print(f"  Reached level {target_level}.")
            return True

        if is_low_hp(stats) or is_winded(stats):
            print("  Resting...")
            rest_until_ready(data_dir)
            continue

        look_out = run("look", data_dir, wait=1.0)
        name, _exits, entities = parse_last_room(look_out)
        hostiles = [e for e in entities if not is_safe_npc(e)]

        if hostiles:
            print(f"  Fighting in {name}...")
            fought, _combat_out = try_kill(data_dir, entities)
            if fought:
                run("get all corpse;get all", data_dir, wait=1.0)
                continue

        print(f"  Nothing to fight in {name}, exploring...")
        explore_step(data_dir, visited)


def hunt_monster(data_dir, target_monster, max_rooms=40):
    print(f"=== Hunting for '{target_monster}' ===")
    visited = set()

    for _ in range(max_rooms):
        stats = parse_stats(run("score", data_dir, wait=1.0))
        if is_low_hp(stats):
            rest_until_ready(data_dir)

        out = run("look", data_dir, wait=1.0)
        name, _exits, entities = parse_last_room(out)

        if any(target_monster.lower() in e.lower() for e in entities):
            print(f"  Found {target_monster} in {name}! Attacking...")
            combat_out = run(f"kill {target_monster}", data_dir, wait=8.0)
            low = combat_out.lower()
            if "you receive" in low or "experience" in low:
                run("get all corpse;get all", data_dir, wait=1.0)
                print(f"  >>> {target_monster} defeated! <<<")
                return True
            print("  Fight ended without a clear win, retrying...")
            continue

        explore_step(data_dir, visited)

    print(f"  Could not find {target_monster} after exploring {max_rooms} rooms.")
    print(f"  Check data/world.md's Explored Rooms for leads, or widen the search manually.")
    return False


def main():
    parser = argparse.ArgumentParser(description="Goal-driven grinding bot for play-mud")
    parser.add_argument("--target-level", type=int, default=None,
                         help="Overrides the level from player.md's Goals section")
    parser.add_argument("--target-monster", type=str, default=None,
                         help="Overrides the monster from player.md's Goals section")
    parser.add_argument("--data-dir", type=str, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)
    goal_level, goal_monster = read_goals(args.data_dir)
    target_level = args.target_level or goal_level or 7
    target_monster = args.target_monster or goal_monster

    if not hunt_for_level(args.data_dir, target_level):
        return

    if target_monster:
        hunt_monster(args.data_dir, target_monster)
    else:
        print("No target monster set yet. Once you've identified it (e.g. from world.md "
              "or a scouting run), add it to player.md's '## Goals' as '- Defeat: <name>' "
              "and rerun grind.py.")


if __name__ == "__main__":
    main()
