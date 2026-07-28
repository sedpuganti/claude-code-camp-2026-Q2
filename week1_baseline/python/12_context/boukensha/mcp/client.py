import itertools
import json
import os
import shlex
import shutil
import subprocess


class Error(Exception):
    pass


class Client:
    """A minimal MCP-over-stdio client: it spawns an MCP server as a
    subprocess, performs the initialize handshake, and lets you discover and
    call the tools it advertises. It knows nothing about any particular
    server — command, args, and env are the standard stdio transport config.

        client = Client.spawn("mud-manager", args=["--mcp"])
        for t in client.tools:
            print(t["name"])
        print(client.call_tool("look")["text"])
        client.close()
    """

    PROTOCOL_VERSION = "2025-06-18"

    @classmethod
    def spawn(cls, command, args=(), env=None):
        return cls(command, args=args, env=env)

    def __init__(self, command, args=(), env=None):
        spawn_env = {**os.environ, **{str(k): str(v) for k, v in (env or {}).items()}}
        cmd = self._spawn_command(command, args, spawn_env)
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=spawn_env,
            text=True,
            bufsize=1,
        )
        self._ids = itertools.count(1)
        self.server_info = None
        self.tools = []
        self._handshake()
        self.tools = self._fetch_tools()

    @staticmethod
    def _spawn_command(command, args, env):
        """Build Windows-safe argv for MCP server wrapper executables."""
        command = str(command)
        argv = [command, *(str(a) for a in args)]
        if os.name != "nt":
            return argv

        executable = Client._which_exact(command, env.get("PATH"))
        if executable is None:
            return argv
        extension = os.path.splitext(executable)[1].lower()
        if extension in (".cmd", ".bat"):
            command_processor = env.get("COMSPEC") or shutil.which("cmd.exe")
            return [command_processor, "/d", "/s", "/c", executable, *argv[1:]]
        if extension:
            return [executable, *argv[1:]]

        try:
            with open(executable, encoding="utf-8") as script:
                first_line = script.readline().strip()
        except (OSError, UnicodeError):
            return argv
        if not first_line.startswith("#!"):
            return argv

        shebang = shlex.split(first_line[2:].strip(), posix=True)
        if not shebang:
            return argv
        if os.path.basename(shebang[0]) == "env" and len(shebang) > 1:
            shebang = shebang[1:]
        interpreter = shutil.which(shebang[0], path=env.get("PATH"))
        if interpreter is None:
            return argv
        return [interpreter, *shebang[1:], executable, *argv[1:]]

    @staticmethod
    def _which_exact(command, path):
        resolved = shutil.which(command, path=path)
        if resolved is not None or os.path.dirname(command):
            return resolved
        for directory in (path or os.defpath).split(os.pathsep):
            candidate = os.path.join(directory.strip('"'), command)
            if os.path.isfile(candidate):
                return candidate
        return None

    def call_tool(self, name, arguments=None):
        res = self._request("tools/call", {"name": str(name), "arguments": arguments or {}})
        result = res.get("result")
        if result is None:
            raise Error(f"tools/call error: {res.get('error')!r}")
        content = result.get("content") or []
        text = "\n".join(c["text"] for c in content if c.get("text") is not None)
        if not content and result.get("text") is not None:
            text = str(result["text"])
        return {"text": text, "error": bool(result.get("isError"))}

    def close(self):
        try:
            self._process.stdin.close()
        except Exception:
            pass
        self._process.wait()
        try:
            self._process.stdout.close()
        except Exception:
            pass
        try:
            self._process.stderr.close()
        except Exception:
            pass

    def _handshake(self):
        from .. import __version__

        res = self._request(
            "initialize",
            {
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "boukensha", "version": __version__},
            },
        )
        self.server_info = (res.get("result") or {}).get("serverInfo")
        self._notify("notifications/initialized")

    def _fetch_tools(self):
        res = self._request("tools/list")
        return (res.get("result") or {}).get("tools") or []

    def _request(self, method, params=None):
        request_id = next(self._ids)
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})
        return self._read_until(request_id)

    def _notify(self, method, params=None):
        self._write({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _write(self, obj):
        self._process.stdin.write(json.dumps(obj) + "\n")
        self._process.stdin.flush()

    def _read_until(self, request_id):
        while True:
            line = self._process.stdout.readline()
            if line == "":
                raise Error(f"server closed the connection{self._stderr_detail()}")
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            if msg.get("id") == request_id:
                return msg
            # ignore server-initiated notifications / mismatched ids

    def _stderr_detail(self):
        try:
            self._process.wait()
            output = self._process.stderr.read()
        except Exception:
            return ""
        return f" — stderr: {output.strip()}" if output and output.strip() else ""
