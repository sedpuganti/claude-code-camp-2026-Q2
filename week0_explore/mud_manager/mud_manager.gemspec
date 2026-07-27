require_relative "lib/mud_manager/version"

Gem::Specification.new do |spec|
  spec.name        = "mud_manager"
  spec.version     = MudManager::VERSION
  spec.summary     = "MudManager — CircleMUD sessions, command primitives, and an MCP daemon"
  spec.description = "Provides MudManager::Session (a long-lived telnet connection with " \
                     "background buffering and IAC stripping) and MudManager::Primitives " \
                     "(typed CircleMUD command builders), exposed to any language through " \
                     "a dependency-free MCP daemon."
  spec.authors     = ["Andrew Brown"]
  spec.email       = ["andrew@exampro.co"]
  spec.license     = "MIT"

  spec.required_ruby_version = ">= 3.0"

  spec.files       = Dir["lib/**/*.rb"] +
                     ["bin/mud-manager", "primitives.json", "README.md"]
  spec.bindir      = "bin"
  spec.executables = ["mud-manager"]

  # No external dependencies — socket and thread are stdlib.
end
