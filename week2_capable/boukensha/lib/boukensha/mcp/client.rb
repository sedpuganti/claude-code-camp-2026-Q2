require "open3"
require "json"
require "rbconfig"

module Boukensha
  module Mcp
    # Client is a minimal MCP-over-stdio client: it spawns an MCP server as a
    # subprocess, performs the initialize handshake, and lets you discover and
    # call the tools it advertises. It knows nothing about any particular
    # server — command, args, and env are the standard stdio transport config.
    #
    #   client = Boukensha::Mcp::Client.spawn(command: "mud-manager", args: ["--mcp"])
    #   client.tools.each { |t| puts t["name"] }
    #   puts client.call_tool("look")[:text]
    #   client.close
    class Client
      class Error < StandardError; end

      PROTOCOL_VERSION = "2025-06-18".freeze
      STARTUP_TIMEOUT = 10

      attr_reader :server_info, :tools

      # command: executable to spawn. args: argv for it. env: extra environment
      # (e.g. a server's credentials — the stdio transport's standard channel).
      def self.spawn(command:, args: [], env: {})
        new(command: command, args: args, env: env)
      end

      def initialize(command:, args: [], env: {})
        cmd = [resolve_command(command.to_s), *Array(args).map(&:to_s)]
        env = env.each_with_object({}) { |(k, v), h| h[k.to_s] = expand_env(v.to_s) }
        spawn_unbundled { @stdin, @stdout, @stderr, @wait = Open3.popen3(env, *cmd) }
        @id = 0
        handshake
        @tools = fetch_tools
      end

      # Substitute ${VAR} in an `env:` value from this process's own
      # environment, so settings.yaml can write a path relative to something
      # stable instead of the shell's cwd:
      #
      #   MUD_TELNET_LOG_DIR: ${BOUKENSHA_DIR}/telnet
      #
      # BOUKENSHA_DIR is exported by BoukenshaLoader before anything spawns
      # (from ~/.boukensharc, or ~/.boukensha), which is the same directory
      # mud_monitor resolves — a bare `.boukensha/telnet` instead lands
      # wherever you happened to launch from, and reads to the monitor as
      # "logging disabled".
      #
      # An unset variable is left verbatim rather than blanked: silently
      # collapsing to "/telnet" would create a directory at the filesystem
      # root, whereas the literal "${BOUKENSHA_DIR}/telnet" fails visibly.
      def expand_env(value)
        value.gsub(/\$\{(\w+)\}/) { ENV.fetch(::Regexp.last_match(1), ::Regexp.last_match(0)) }
      end

      # Call a tool. Returns { text:, error: (bool) }.
      #
      # `meta:` rides in the MCP-spec `_meta` slot on the params (spec-legal,
      # additive, ignored by any server that doesn't read it) — the boukensha
      # session/operation id, so a server that logs its own side of the
      # exchange can stamp the same correlation id rather than a reader
      # matching two logs by timestamp adjacency.
      def call_tool(name, arguments = {}, meta: nil)
        params = { "name" => name.to_s, "arguments" => arguments }
        params["_meta"] = meta if meta && !meta.empty?
        res = request("tools/call", params)
        result = res["result"] or raise Error, "tools/call error: #{res["error"].inspect}"
        text = Array(result["content"]).map { |c| c["text"] }.compact.join("\n")
        { text: text, error: !!result["isError"] }
      end

      def close
        @stdin.close rescue nil
        @wait&.value
        @stdout.close rescue nil
        @stderr.close rescue nil
      end

      private

      # Prefer Windows-native wrappers over extensionless POSIX shims. Without
      # this, Process.spawn may select `npx` instead of `npx.cmd` and leave the
      # MCP initialization request waiting forever under Git Bash.
      def resolve_command(command)
        return command unless Gem.win_platform?
        return command if command.match?(%r{[\\/]}) || !File.extname(command).empty?

        extensions = ENV.fetch("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
        ENV.fetch("PATH", "").split(File::PATH_SEPARATOR).each do |directory|
          directory = directory.delete_prefix('"').delete_suffix('"')
          extensions.each do |extension|
            [extension.downcase, extension.upcase].each do |candidate_extension|
              candidate = File.join(directory, "#{command}#{candidate_extension}")
              return candidate if File.file?(candidate)
            end
          end
        end
        command
      end

      # An MCP server is a separate program with its own dependencies — it may
      # not even be a Ruby process. If *boukensha itself* is running under
      # Bundler (e.g. launched via `bundle exec`), BUNDLE_GEMFILE/RUBYOPT would
      # otherwise leak into the spawned server's environment and force it to
      # activate boukensha's bundle instead of its own, which fails outright
      # for a server whose gems aren't in that Gemfile (a double "already
      # initialized constant Gem::Platform::..." warning from rubygems_ext
      # loading twice is the telltale sign).
      #
      # Nil-ing BUNDLE_GEMFILE/RUBYOPT in the env hash passed to Open3.popen3
      # does NOT work here: once Bundler.setup has run in *this* process, it
      # patches Process.spawn to always re-inject its own captured env into
      # every child, overriding explicit unsets. Bundler.with_unbundled_env is
      # its own sanctioned escape hatch for exactly this case — it restores
      # the environment Bundler captured before activating itself. A no-op
      # when Bundler was never loaded (boukensha run outside `bundle exec`).
      def spawn_unbundled(&block)
        if defined?(Bundler)
          Bundler.with_unbundled_env(&block)
        else
          block.call
        end
      end

      def handshake
        res = request("initialize", {
          "protocolVersion" => PROTOCOL_VERSION,
          "capabilities"    => {},
          "clientInfo"      => { "name" => "boukensha", "version" => Boukensha::VERSION }
        }, timeout: STARTUP_TIMEOUT)
        @server_info = res.dig("result", "serverInfo")
        notify("notifications/initialized")
      end

      def fetch_tools
        request("tools/list", timeout: STARTUP_TIMEOUT).dig("result", "tools") || []
      end

      def request(method, params = {}, timeout: nil)
        id = (@id += 1)
        write({ "jsonrpc" => "2.0", "id" => id, "method" => method, "params" => params })
        read_until(id, timeout: timeout)
      end

      def notify(method, params = {})
        write({ "jsonrpc" => "2.0", "method" => method, "params" => params })
      end

      def write(obj)
        @stdin.puts(JSON.generate(obj))
        @stdin.flush
      end

      def read_until(id, timeout: nil)
        deadline = timeout && Process.clock_gettime(Process::CLOCK_MONOTONIC) + timeout
        loop do
          if deadline
            remaining = deadline - Process.clock_gettime(Process::CLOCK_MONOTONIC)
            startup_timeout! if remaining <= 0 || !IO.select([@stdout], nil, nil, remaining)
          end
          line = @stdout.gets
          raise Error, "server closed the connection#{stderr_detail}" if line.nil?
          line = line.strip
          next if line.empty?
          msg = JSON.parse(line)
          return msg if msg["id"] == id
          # ignore server-initiated notifications / mismatched ids
        end
      end

      def startup_timeout!
        @stdin.close rescue nil
        @stdout.close rescue nil
        @stderr.close rescue nil
        Process.kill("KILL", @wait.pid) if @wait&.alive?
        @wait&.value
        raise Error, "server did not complete MCP startup within #{STARTUP_TIMEOUT} seconds"
      rescue Errno::ESRCH
        raise Error, "server did not complete MCP startup within #{STARTUP_TIMEOUT} seconds"
      end

      # Drains whatever the subprocess wrote to stderr before it died, so a
      # crash during spawn/handshake (bad Ruby version, missing gem,
      # unhandled exception before the request loop starts) is diagnosable
      # instead of a bare "server closed the connection". @stdout hitting EOF
      # means the process is exiting or has exited, so @wait.value (bounded —
      # it's already at EOF) reaps it and guarantees @stderr is fully flushed
      # before the blocking read below.
      def stderr_detail
        @wait&.value
        output = @stderr.read
        output && !output.strip.empty? ? " — stderr: #{output.strip}" : ""
      rescue IOError
        ""
      end
    end
  end
end
