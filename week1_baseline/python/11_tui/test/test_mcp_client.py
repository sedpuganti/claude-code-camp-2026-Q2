from boukensha.mcp.client import Client
from unittest.mock import mock_open, patch

from .helper import MUD_MANAGER_ARGS, MUD_MANAGER_COMMAND, McpTestCase


# boukensha.mcp.client.Client is boukensha's own MCP-over-stdio client. It is
# server-agnostic: it takes a command, args, and env, and speaks the
# protocol. We point it at the mud-manager daemon because that is the MCP
# server this repo ships — nothing in the client knows that.
class TestMcpClient(McpTestCase):
    def setUp(self):
        self.fake = self.start_fake_mud()
        self.client = None

    def tearDown(self):
        if self.client is not None:
            self.client.close()
        self.fake.stop()

    def spawn_client(self):
        self.client = Client.spawn(
            MUD_MANAGER_COMMAND, args=MUD_MANAGER_ARGS, env=self.fake_mud_env(self.fake)
        )
        return self.client

    def test_handshake_reports_server_info(self):
        client = self.spawn_client()
        self.assertEqual("mud-manager", client.server_info["name"])
        self.assertIsNotNone(client.server_info["version"])

    def test_tools_list_is_discovered(self):
        client = self.spawn_client()
        names = [t["name"] for t in client.tools]
        self.assertIn("look", names)
        self.assertIn("attack", names)
        # Discovery is the server's word, not ours — the client invents nothing.
        self.assertGreater(len(client.tools), 1)
        self.assertTrue(all("inputSchema" in t for t in client.tools))

    def test_call_tool_reaches_the_mud(self):
        client = self.spawn_client()
        self.assertIn("You do: look", client.call_tool("look")["text"])
        self.assertIn(
            "You do: kill dragon", client.call_tool("attack", {"target": "dragon"})["text"]
        )

    # A tool-level failure is data (isError), not an exception — the agent
    # loop must be able to keep going.
    def test_tool_error_comes_back_as_data(self):
        client = self.spawn_client()
        result = client.call_tool("move", {"direction": "sideways"})
        self.assertTrue(result["error"], "expected isError to be set")
        self.assertIn("argument_error", result["text"])

    def test_spawning_a_nonexistent_command_raises(self):
        with self.assertRaises(FileNotFoundError):
            Client.spawn("boukensha-no-such-mcp-server-xyz")


class TestWindowsCommandResolution(McpTestCase):
    def test_extensionless_shebang_uses_interpreter(self):
        env = {"PATH": r"C:\Ruby40-x64\bin"}
        with patch("boukensha.mcp.client.os.name", "nt"), patch.object(
            Client, "_which_exact", return_value=r"C:\Ruby40-x64\bin\mud-manager"
        ), patch(
            "boukensha.mcp.client.shutil.which",
            return_value=r"C:\Ruby40-x64\bin\ruby.exe",
        ), patch(
            "builtins.open", mock_open(read_data="#!/usr/bin/env ruby\n")
        ):
            cmd = Client._spawn_command("mud-manager", ["--mcp"], env)

        self.assertEqual(
            [
                r"C:\Ruby40-x64\bin\ruby.exe",
                r"C:\Ruby40-x64\bin\mud-manager",
                "--mcp",
            ],
            cmd,
        )


class TestToolResultCompatibility(McpTestCase):
    def test_reads_legacy_top_level_text_result(self):
        client = object.__new__(Client)
        client._request = lambda method, params: {
            "result": {"text": "Market Square\nExits: north", "isError": False}
        }

        self.assertEqual(
            {"text": "Market Square\nExits: north", "error": False},
            client.call_tool("look"),
        )
