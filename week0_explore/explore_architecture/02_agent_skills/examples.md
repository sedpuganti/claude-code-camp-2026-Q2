# MUD Client Usage Examples

## Interactive Play Session

```bash
# Start the client
mud-play.bat

# At the prompt (once logged in), type commands:
> look
> inventory
> north
> say Hello everyone!
> who
> cast 'magic missile' target
> kill enemy
> quit
```

## Single Command Execution

### Windows
```bash
# Check surroundings
mud-play.bat look

# Check inventory
mud-play.bat inventory

# Get status
mud-play.bat score

# See who's online
mud-play.bat who

# Cast a spell (quoted for spaces)
mud-play.bat "cast 'magic missile' target"

# Emote
mud-play.bat "emote waves"

# Send a message
mud-play.bat "say Hello!"
```

### Linux/Mac
```bash
./mud-play.sh look
./mud-play.sh inventory
./mud-play.sh "cast 'magic missile' target"
```

## Batch Automation

Create a `play-sequence.bat` file:

```batch
@echo off
echo === MUD Automation Example ===
echo Checking location...
call mud-play.bat look

echo.
echo Checking inventory...
call mud-play.bat inventory

echo.
echo Checking status...
call mud-play.bat score

echo.
echo Saying hello...
call mud-play.bat "say Hello from automation!"

echo.
echo Getting player list...
call mud-play.bat who

echo.
echo Done!
```

Run it:
```bash
play-sequence.bat
```

## Logging Output

Capture output to a file:

```bash
# Windows
mud-play.bat look > look-output.txt
mud-play.bat inventory >> look-output.txt

# Linux/Mac
./mud-play.sh look > look-output.txt
./mud-play.sh inventory >> look-output.txt
```

## Scheduled Tasks (Windows)

Create a scheduled task to check character status every hour:

```batch
@echo off
REM Check MUD status and log it
echo [%date% %time%] >> mud-status.log
mud-play.bat score >> mud-status.log
mud-play.bat who >> mud-status.log
echo. >> mud-status.log
```

## Integration with Claude Code

### Via terminal
```bash
# Open terminal and run
node mud-client.js

# Or use the batch file
mud-play.bat
```

### Via Claude Code prompt
You can reference the mud client in your Claude Code workflow:
```bash
! mud-play.bat look
! mud-play.bat inventory
```

## Advanced Examples

### Check character state and log it
```batch
@echo off
setlocal enabledelayedexpansion
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set date=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set time=%%a%%b)

echo [!date! !time!] Checking MUD status...
echo Timestamp: !date! !time! >> character.log
mud-play.bat score >> character.log
echo. >> character.log
```

### Continuous monitoring (runs every 5 minutes)
```batch
@echo off
:loop
cls
echo Checking MUD status at %time%...
mud-play.bat look
timeout /t 300 /nobreak
goto loop
```

### Parse and store results
```batch
@echo off
for /f "delims=" %%a in ('mud-play.bat look') do (
  set result=%%a
  echo !result! >> mud-log.txt
)
```

## Troubleshooting Examples

### Test connection
```bash
# Should show your current location
mud-play.bat look

# Should show your stats
mud-play.bat score

# Should list online players
mud-play.bat who
```

### Debug mode
Edit mud-client.js and uncomment logging:
```javascript
// Add this after receiving data:
console.error('[DEBUG]', data.toString());
```

### Network issues
```bash
# Test if server is reachable
ping localhost

# Test port 4000 (requires PowerShell)
Test-NetConnection -ComputerName localhost -Port 4000
```

## Environment Variables

You can extend mud-client.js to use environment variables:

```javascript
const HOST = process.env.MUD_HOST || 'localhost';
const PORT = process.env.MUD_PORT || 4000;
const USERNAME = process.env.MUD_USER || 'dummy';
const PASSWORD = process.env.MUD_PASS || 'helloworld';
```

Then use:
```bash
set MUD_HOST=myserver.com
set MUD_PORT=5000
set MUD_USER=mychar
set MUD_PASS=mypass
mud-play.bat
```

## Real-World Use Cases

### Daily character status report
Create `daily-report.bat`:
```batch
@echo off
echo Daily Character Report
echo ========================
echo.
echo Current Location:
mud-play.bat look
echo.
echo Character Stats:
mud-play.bat score
echo.
echo Online Players:
mud-play.bat who
```

### Idle monitoring
```batch
@echo off
:check
cls
echo Monitoring %date% %time%
mud-play.bat look > current.txt
echo.
echo Waiting 10 minutes...
timeout /t 600
goto check
```

### Combat logging
```batch
@echo off
echo === Combat Session %date% %time% ===
mud-play.bat look
REM Now switch to interactive mode for real combat
mud-play.bat
```
