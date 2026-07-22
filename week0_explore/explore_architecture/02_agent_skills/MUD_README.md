# tbaMUD Client

A Node.js-based telnet client for playing tbaMUD on localhost:4000 with automatic login support.

## Quick Start

### Prerequisites
- Node.js installed (v12+)
- tbaMUD running on localhost:4000
- Player account: `dummy` / `helloworld`

### Usage

#### Interactive Mode (Windows)
```bash
mud-play.bat
```

Or directly with Node:
```bash
node mud-client.js
```

#### Interactive Mode (Linux/Mac)
```bash
chmod +x mud-client.js
./mud-client.js
```

#### Single Command Mode
Execute a command and disconnect:
```bash
# Windows
mud-play.bat look
mud-play.bat inventory
mud-play.bat "cast 'magic missile'"

# Linux/Mac
./mud-client.js look
./mud-client.js inventory
./mud-client.js "cast 'magic missile'"
```

## Features

✅ **Automatic Login** - Logs in with dummy/helloworld credentials automatically
✅ **Interactive Console** - Type commands directly (supports full CircleMUD command set)
✅ **Single Command Mode** - Execute a command and exit
✅ **Telnet Protocol** - Proper telnet connection to localhost:4000
✅ **Error Handling** - Graceful error messages and reconnection handling

## File Structure

```
├── mud-client.js           # Main telnet client script
├── mud-play.bat            # Windows batch launcher
├── package.json            # Node.js package info
└── MUD_README.md          # This file
```

## Configuration

To change credentials or connection details, edit `mud-client.js`:

```javascript
const HOST = 'localhost';      // Change server host
const PORT = 4000;             // Change server port
const USERNAME = 'dummy';      // Change username
const PASSWORD = 'helloworld'; // Change password
```

## Common MUD Commands

### Navigation
- `north`, `south`, `east`, `west`, `up`, `down` - Move in a direction
- `look` - Look around current location
- `examine <object>` - Examine something closely

### Character
- `inventory` - View your inventory
- `score` - View character stats
- `equipment` - View equipped items
- `who` - See online players

### Communication
- `say <message>` - Speak in the room
- `emote <action>` - Perform an action (e.g., `emote waves`)
- `tell <player> <message>` - Send a private message

### Combat & Magic
- `kill <target>` - Attack someone
- `cast <spell>` - Cast a spell (e.g., `cast 'magic missile'`)
- `flee` - Run away from combat
- `assist <player>` - Help in combat

### Items & Inventory
- `get <object>` - Pick up an object
- `drop <object>` - Drop an item
- `give <object> <player>` - Give item to someone
- `wield <weapon>` - Equip a weapon
- `wear <armor>` - Put on armor

### Misc
- `help <topic>` - Get help on a topic
- `time` - Check game time
- `weather` - Check weather
- `quit` - Log off (or `exit`)

## Troubleshooting

### "Connection refused"
- Ensure tbaMUD is running on localhost:4000
- Check firewall settings

### "Connection timeout"
- Verify localhost:4000 is accessible
- Try restarting the MUD server

### Slow response times
- This is normal for network-based MUDs
- Add delays in scripts if needed

### Commands not working
- Wait for the game prompt (>) before typing
- Check that you're logged in properly
- Some commands may not be available to new characters

## Examples

### Example 1: Quick Status Check
```bash
mud-play.bat look
```

### Example 2: Interactive Session
```bash
mud-play.bat
> look
> inventory
> say Hello world!
> emote waves at everyone
> quit
```

### Example 3: Multiple Commands
```bash
# In interactive mode, type multiple commands:
mud-play.bat
> north
> look
> say Hi there!
> south
> quit
```

## Advanced Usage

### Scripting Commands
You can chain commands together in a batch file:

**play.bat**
```batch
@echo off
echo Executing MUD commands...
node mud-client.js look
node mud-client.js inventory
node mud-client.js "say Hello from automation!"
```

### Piping Output
```bash
node mud-client.js look > output.txt
```

## Development

The mud-client.js uses Node.js built-in `net` module for socket communication:
- Handles telnet connection negotiation
- Auto-detects login prompts
- Manages stdin/stdout for interactive mode
- Parses command-line arguments for single-command mode

## License

MIT License - Feel free to modify and use this client for tbaMUD.

## Support

For issues with the MUD itself, contact your tbaMUD administrator.
For client script issues, check that Node.js is properly installed.
