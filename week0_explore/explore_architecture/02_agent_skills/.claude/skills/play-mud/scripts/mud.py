#!/usr/bin/env python3
"""
MUD Client — connects to tbaMUD on localhost:4000 and executes commands.

Usage:
  python3 mud.py "<command>"
  python3 mud.py "cmd1;cmd2;cmd3"
  python3 mud.py "cmd1;cmd2" --wait 2.0
  python3 mud.py "score;look;eq" --data-dir ./data
"""

import argparse
import os
import re
import select
import socket
import time
import sys

HOST = "localhost"
PORT = 4000
USERNAME = "dummy"
PASSWORD = "helloworld"
SOCKET_TIMEOUT = 15
CMD_DELAY = 0.4
RECV_TIMEOUT = 1.8
PROMPT_WAIT = 2.5


def strip_ansi(text: str) -> str:
    """Remove ANSI color codes and telnet control sequences."""
    # Remove ANSI color codes
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    # Remove telnet IAC sequences
    text = re.sub(r"\xff[\xf0-\xfe]", "", text)
    # Remove other control characters except newline, tab, carriage return
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return text


def load_memory(data_dir: str) -> dict:
    memory = {}
    for name in ("player", "world"):
        path = os.path.join(data_dir, f"{name}.md")
        if os.path.exists(path):
            with open(path) as f:
                memory[name] = f.read()
        else:
            memory[name] = ""
    return memory


def update_player_memory(data_dir: str, output: str, existing: str):
    """Parse score output and update player.md with current stats."""
    lines = output.split("\n")
    updates = {}

    for line in lines:
        m = re.match(r"You are (\d+) years old", line)
        if m:
            updates["age"] = m.group(1)

        m = re.match(r"You have (\d+)\((\d+)\) hit, (\d+)\((\d+)\) mana and (\d+)\((\d+)\) movement", line)
        if m:
            updates["hp_cur"], updates["hp_max"] = m.group(1), m.group(2)
            updates["mana_cur"], updates["mana_max"] = m.group(3), m.group(4)
            updates["mv_cur"], updates["mv_max"] = m.group(5), m.group(6)

        m = re.match(r"Your armor class is ([\d/]+)", line)
        if m:
            updates["ac"] = m.group(1)

        m = re.match(r"Your alignment is (-?\d+)", line)
        if m:
            updates["alignment"] = m.group(1)

        m = re.match(r"You have (\d+) exp", line)
        if m:
            updates["xp"] = m.group(1)

        m = re.match(r"You have (\d+) gold coins", line)
        if m:
            updates["gold"] = m.group(1)

        m = re.match(r"You need (\d+) exp to reach your next level", line)
        if m:
            updates["xp_next"] = m.group(1)

        m = re.match(r"This ranks you as .+ \(level (\d+)\)", line)
        if m:
            updates["level"] = m.group(1)

        m = re.match(r"You have been playing for (\d+) days and (\d+) hours", line)
        if m:
            updates["played_days"] = m.group(1)
            updates["played_hours"] = m.group(2)

    if not updates:
        return existing

    header = "## Player Memory (auto-updated from score)"
    body = existing
    if header in body:
        body = body.replace(header, "").strip()

    for key, val in updates.items():
        line_prefix = f"- {key}: "
        found = False
        for old_line in body.split("\n"):
            if old_line.startswith(line_prefix):
                body = body.replace(old_line, f"{line_prefix}{val}")
                found = True
                break
        if not found:
            body += f"\n{line_prefix}{val}"

    return f"{header}\n{body.strip()}\n"


def parse_room_from_output(block: str):
    """Extract (room_name, desc_lines, exits_line, entity_lines) from one `look`-shaped
    chunk of output (i.e. one command's worth, not a whole multi-command run)."""
    lines = block.split("\n")
    room_name = ""
    desc_lines = []
    exits_line = ""
    entity_lines = []
    state = "seek_name"

    for line in lines:
        stripped = line.strip()
        if state == "seek_name":
            if stripped and re.match(r"^[A-Z][A-Za-z' ]+$", stripped):
                room_name = stripped
                state = "desc"
            continue
        if state == "desc":
            if stripped.startswith("[ Exits:"):
                exits_line = stripped
                state = "post_exits"
            elif stripped:
                desc_lines.append(stripped)
            continue
        if state == "post_exits":
            if not stripped:
                continue
            if re.match(r"^\d+H\s+\d+M\s+\d+V", stripped):
                break  # hit the next command prompt; this room block is done
            entity_lines.append(stripped)

    return room_name, desc_lines, exits_line, entity_lines


def parse_explored_rooms(section_text: str) -> dict:
    """Parse existing '### RoomName' blocks (as written by render_rooms) back into a dict."""
    rooms = {}
    for block in re.split(r"\n(?=### )", section_text):
        m = re.match(r"### (.+)", block.strip())
        if not m:
            continue
        name = m.group(1).strip()
        desc_m = re.search(r"- desc: (.*)", block)
        exits_m = re.search(r"- exits: (.*)", block)
        ent_m = re.search(r"- entities: (.*)", block)
        rooms[name] = {
            "desc": desc_m.group(1).strip() if desc_m else "",
            "exits": exits_m.group(1).strip() if exits_m else "",
            "entities": ent_m.group(1).strip() if ent_m else "",
        }
    return rooms


def render_rooms(rooms: dict) -> str:
    blocks = []
    for name in sorted(rooms):
        r = rooms[name]
        block = f"### {name}\n- desc: {r.get('desc', '')}\n- exits: {r.get('exits', '')}"
        if r.get("entities"):
            block += f"\n- entities: {r['entities']}"
        blocks.append(block)
    return "\n\n".join(blocks)


def update_world_memory(data_dir: str, output: str, existing: str):
    """Parse every room seen in this run's output and merge it into an accumulating
    'Explored Rooms' catalog, keyed by room name, so the map grows across invocations
    instead of being overwritten by whichever room was looked at last."""
    header = "## World Memory (auto-updated from look)"

    existing_section = ""
    if existing and header in existing:
        m = re.search(re.escape(header) + r"(.*?)(?=\n## |\Z)", existing, re.DOTALL)
        if m:
            existing_section = m.group(1)

    rooms = parse_explored_rooms(existing_section)

    found_any = False
    for block in output.split("\n---\n"):
        room_name, desc_lines, exits_line, entity_lines = parse_room_from_output(block)
        if not room_name:
            continue
        found_any = True
        prior = rooms.get(room_name, {})
        rooms[room_name] = {
            "desc": " ".join(desc_lines) if desc_lines else prior.get("desc", ""),
            "exits": exits_line.strip() if exits_line else prior.get("exits", ""),
            "entities": " | ".join(entity_lines) if entity_lines else "",
        }

    if not found_any:
        return existing

    new_section = f"{header}\n\n{render_rooms(rooms)}\n"

    if existing and header in existing:
        return re.sub(re.escape(header) + r".*?(?=\n## |\Z)", new_section, existing, flags=re.DOTALL)

    if existing:
        sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
        return f"{existing}{sep}{new_section}"

    return new_section


def save_memory(data_dir: str, output: str, old_memory: dict):
    os.makedirs(data_dir, exist_ok=True)

    player = update_player_memory(data_dir, output, old_memory.get("player", ""))
    world = update_world_memory(data_dir, output, old_memory.get("world", ""))

    for name, content in [("player", player), ("world", world)]:
        path = os.path.join(data_dir, f"{name}.md")
        if content:
            with open(path, "w") as f:
                f.write(content + "\n")

    output_path = os.path.join(data_dir, "last_output.txt")
    with open(output_path, "w") as f:
        f.write(output)


class MudClient:
    def __init__(self):
        self.sock = None

    def connect(self):
        """Connect to MUD with improved error handling."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        try:
            self.sock.connect((HOST, PORT))
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            raise RuntimeError(f"Failed to connect to {HOST}:{PORT}: {e}")

    def _recv(self, timeout: float = RECV_TIMEOUT) -> str:
        """Receive data from socket with improved handling."""
        data = b""
        deadline = time.time() + timeout
        got_any_data = False

        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            try:
                # Use a longer select timeout to allow MUD more time to send data
                select_timeout = min(remaining, 0.5)
                ready, _, _ = select.select([self.sock], [], [], select_timeout)
                if ready:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    got_any_data = True
                    # Keep receiving if more data arrives quickly
                    continue
                elif got_any_data:
                    # We got some data and nothing more is coming quickly, we're done
                    break
            except (socket.timeout, OSError) as e:
                break

        try:
            return data.decode(errors="replace")
        except Exception:
            return data.decode("utf-8", errors="replace")

    def _send(self, text: str, delay: float = CMD_DELAY):
        """Send command and wait for response."""
        try:
            self.sock.sendall((text + "\n").encode())
            time.sleep(delay)
        except (socket.timeout, OSError, BrokenPipeError) as e:
            raise RuntimeError(f"Failed to send command: {e}")

    def login(self):
        """Login to the MUD with improved handling."""
        # Receive initial banner
        self._recv(PROMPT_WAIT)

        # Send username
        self._send(USERNAME, 0.5)
        self._recv(1.0)

        # Confirm character name by repeating the username
        self._send(USERNAME, 0.5)
        self._recv(1.0)

        # Send password (for both new and existing characters)
        self._send(PASSWORD, 0.5)
        output = self._recv(1.0)

        # If password was rejected or needs retype, send again
        if "retype" in output.lower() or "again" in output.lower() or "match" in output.lower():
            self._send(PASSWORD, 0.5)
            self._recv(PROMPT_WAIT)

        # Wait for character to fully load into game
        time.sleep(1.5)

    def execute(self, commands: str, wait: float = None) -> str:
        """Execute one or more commands separated by semicolon."""
        parts = [c.strip() for c in commands.split(";") if c.strip()]
        results = []

        for cmd in parts:
            delay = wait if wait else CMD_DELAY
            self._send(cmd, delay)

            # Determine timeout: longer for movement, shorter for info commands
            if cmd.lower() in ["n", "s", "e", "w", "u", "d", "north", "south", "east", "west", "up", "down"]:
                recv_timeout = RECV_TIMEOUT
            else:
                recv_timeout = RECV_TIMEOUT if not wait else wait

            out = self._recv(recv_timeout)
            cleaned = strip_ansi(out)
            results.append(cleaned)

            # Add a small pause between commands to ensure proper processing
            if len(parts) > 1:
                time.sleep(0.2)

        return "\n---\n".join(results)

    def close(self):
        """Close socket connection cleanly."""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except (OSError, BrokenPipeError):
                pass
            try:
                self.sock.close()
            except (OSError, BrokenPipeError):
                pass
            self.sock = None


def main():
    parser = argparse.ArgumentParser(description="MUD Client for tbaMUD")
    parser.add_argument("commands", nargs="?", default="look", help="Command(s) to execute. Use ; to separate multiple commands.")
    parser.add_argument("--wait", type=float, default=None, help="Extra wait time between commands (seconds)")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory for persistent memory (player.md, world.md)")
    args = parser.parse_args()

    memory = {}
    if args.data_dir:
        memory = load_memory(args.data_dir)

    client = MudClient()
    try:
        client.connect()
        client.login()

        if memory.get("player"):
            print(f"[Memory] Player state loaded from {args.data_dir}/player.md")
        if memory.get("world"):
            print(f"[Memory] World state loaded from {args.data_dir}/world.md")

        output = client.execute(args.commands, args.wait)
        print(output)

        if args.data_dir:
            save_memory(args.data_dir, output, memory)
            print(f"[Memory] State saved to {args.data_dir}/")
    except (socket.timeout, BrokenPipeError, ConnectionResetError) as e:
        print(f"[Error] Connection failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[Error] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
