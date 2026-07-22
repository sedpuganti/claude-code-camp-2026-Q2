# Claude Code Skill Integration Guide

This document explains how to use and integrate the tbaMUD client as a Claude Code skill.

## Current Setup

The MUD client is available as:

### Method 1: Direct Node.js Execution
```bash
node mud-client.js [command]
node mud-client.js                    # Interactive mode
node mud-client.js look               # Single command mode
```

### Method 2: Batch File (Windows)
```bash
mud-play.bat [command]
mud-play.bat                          # Interactive mode
mud-play.bat look                     # Single command mode
mud-play.bat inventory
```

### Method 3: Shell Script (Linux/Mac)
```bash
./mud-play.sh [command]
./mud-play.sh                         # Interactive mode
./mud-play.sh look                    # Single command mode
```

## Using in Claude Code

### From Terminal
In Claude Code's integrated terminal, you can run:

```bash
# Windows
mud-play.bat look

# Linux/Mac  
./mud-play.sh look
```

Or directly with Node:
```bash
node mud-client.js look
```

### From Claude Code Prompts

When Claude Code needs to execute MUD commands, it can use:

```bash
! mud-play.bat look
! mud-play.bat inventory
! mud-play.bat "cast 'magic missile'"
```

The `!` prefix runs commands in the Claude Code shell.

## Files Included

### Core Files
- **mud-client.js** - Main telnet client (Node.js)
- **mud-play.bat** - Windows launcher
- **mud-play.sh** - Linux/Mac launcher
- **package.json** - Node.js configuration

### Configuration
- **mud-config.json** - Server and credential settings
- **.claude/skills/mud-play.md** - Skill documentation

### Documentation
- **MUD_README.md** - Complete usage guide
- **examples.md** - Usage examples and automation
- **SKILL_INTEGRATION.md** - This file

## Customizing Credentials

### Option 1: Edit mud-client.js
```javascript
const USERNAME = 'your-username';
const PASSWORD = 'your-password';
```

### Option 2: Use mud-config.json
Edit the credentials section:
```json
{
  "credentials": {
    "username": "your-username",
    "password": "your-password"
  }
}
```

Then modify mud-client.js to use the config file (requires code update).

### Option 3: Environment Variables
Add this to mud-client.js:
```javascript
const USERNAME = process.env.MUD_USER || 'dummy';
const PASSWORD = process.env.MUD_PASS || 'helloworld';
```

Then set in Claude Code or terminal:
```bash
# Windows
set MUD_USER=mychar
set MUD_PASS=mypass
mud-play.bat

# Linux/Mac
export MUD_USER=mychar
export MUD_PASS=mypass
./mud-play.sh
```

## Advanced Integration

### Running MUD Commands from Scripts

Create a helper script `run-mud-command.js`:

```javascript
const { exec } = require('child_process');

function executeMudCommand(command) {
  return new Promise((resolve, reject) => {
    const child = require('child_process').spawn('node', ['mud-client.js', command]);
    let output = '';
    
    child.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`Command failed: ${command}`));
      }
    });
  });
}

// Usage
executeMudCommand('look').then(result => {
  console.log('MUD Response:', result);
});
```

### Monitoring MUD Status

Create `monitor-mud.js`:

```javascript
const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function logMudStatus() {
  const timestamp = new Date().toISOString();
  const logFile = path.join(__dirname, 'mud-status.log');
  
  const result = spawnSync('node', ['mud-client.js', 'look'], {
    encoding: 'utf-8'
  });
  
  const logEntry = `[${timestamp}] ${result.stdout}\n`;
  fs.appendFileSync(logFile, logEntry);
  
  console.log('Status logged at', timestamp);
}

// Run every 5 minutes
setInterval(logMudStatus, 5 * 60 * 1000);
logMudStatus(); // Run immediately first
```

Run it:
```bash
node monitor-mud.js
```

### Slack Integration

Create `slack-mud-notify.js`:

```javascript
const webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL';
const { spawnSync } = require('child_process');
const https = require('https');

function notifySlack(message) {
  const payload = JSON.stringify({ text: message });
  
  const options = {
    hostname: 'hooks.slack.com',
    path: webhook_url.replace('https://hooks.slack.com', ''),
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': payload.length
    }
  };
  
  https.request(options).write(payload);
}

// Get MUD status and notify
const result = spawnSync('node', ['mud-client.js', 'look'], {
  encoding: 'utf-8'
});

notifySlack(`MUD Status: ${result.stdout}`);
```

## Troubleshooting Integration

### MUD Client Not Found
Make sure you're in the correct directory:
```bash
cd C:\dev\claude-code-camp-2026-Q2\week0_explore\explore_architecture\02_agent_skills
mud-play.bat
```

### Permission Denied (Linux/Mac)
Make the script executable:
```bash
chmod +x mud-play.sh
chmod +x mud-client.js
./mud-play.sh
```

### Node.js Not Found
Install Node.js from nodejs.org or:
```bash
# macOS
brew install node

# Ubuntu/Debian
sudo apt-get install nodejs npm

# Windows
# Download from nodejs.org
```

### Connection Issues
Verify MUD is running:
```bash
# Test port
telnet localhost 4000

# Or in PowerShell
Test-NetConnection -ComputerName localhost -Port 4000
```

## Next Steps

1. **Install Node.js** if you haven't already
2. **Test the connection** with `mud-play.bat look`
3. **Read MUD_README.md** for complete command reference
4. **Check examples.md** for automation ideas
5. **Customize credentials** in mud-client.js as needed
6. **Integrate with your workflow** using the patterns above

## API-Style Usage

For Claude Code agents or scripts that need MUD interaction:

```javascript
// Execute a MUD command and get output
const { spawnSync } = require('child_process');

function queryMUD(command) {
  const result = spawnSync('node', ['mud-client.js', command], {
    encoding: 'utf-8',
    cwd: __dirname
  });
  return result.stdout;
}

// Use it
const location = queryMUD('look');
console.log('You are at:', location);
```

## Security Considerations

### Credentials
- Store real credentials in environment variables, not in code
- Never commit passwords to version control
- Use `.gitignore` for config files with real credentials

### Network
- Only use localhost for development
- For remote servers, use SSH tunneling
- Keep MUD server secure and protected

### Script Execution
- Validate any user input passed to MUD commands
- Be careful with automated scripts that perform actions
- Log all important MUD interactions

## Support & Feedback

- For MUD client issues: Check MUD_README.md
- For integration help: See examples.md
- For customization: Edit mud-client.js or create wrapper scripts
- For bugs: Check the connection and MUD server status first
