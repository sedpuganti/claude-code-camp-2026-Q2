---
name: mud-play
description: Play tbaMUD Interactive Client with auto-login to localhost:4000
trigger: mud-play
executable: ./mud-play.bat
---

# mud-play: tbaMUD Interactive Client

Play tbaMUD (localhost:4000) with automatic login. Uses the mud-client.js script to manage telnet connections and commands.

## Usage

### Interactive mode (default)
Launches an interactive MUD session with automatic login.
```
/mud-play
```

### Execute single command
Execute a command and disconnect.
```
/mud-play look
/mud-play inventory
/mud-play cast 'magic missile'
```

## Features

- **Auto-login**: Automatically connects and authenticates with dummy/helloworld
- **Interactive console**: Type commands directly (type `quit` or `exit` to disconnect)
- **Single command mode**: Pass commands as arguments to execute and disconnect
- **Error handling**: Handles connection failures and disconnections gracefully

## Credentials

- **Host**: localhost
- **Port**: 4000
- **Username**: dummy
- **Password**: helloworld

## Available MUD Commands

Once connected, you can use standard CircleMUD commands:
- `look` - Look around your current location
- `inventory` - View your inventory
- `who` - See who's online
- `help` - Get help on topics
- `cast <spell>` - Cast a spell
- `kill <target>` - Attack someone
- `say <text>` - Speak to others in the room
- `emote <action>` - Perform an emote
- `move <direction>` - Move (north, south, east, west, up, down)
- `quit` - Log off

## Examples

```bash
# Start interactive session
/mud-play

# Check current status
/mud-play look

# Check inventory
/mud-play inventory

# Cast a spell (must be in game)
/mud-play cast 'magic missile'

# Use emote
/mud-play emote waves
```
