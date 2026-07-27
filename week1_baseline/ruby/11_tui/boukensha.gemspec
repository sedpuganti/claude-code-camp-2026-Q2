require_relative "lib/boukensha/version"

Gem::Specification.new do |spec|
  spec.name        = "boukensha"
  spec.version     = Boukensha::VERSION
  spec.summary     = "BOUKENSHA — a tiny teaching framework for coding harnesses"
  spec.description = "Step-by-step coding harness framework. " \
                     "Set BOUKENSHA_PATH to load a specific lesson step, " \
                     "or run with defaults to use the bundled release."
  spec.authors     = ["Andrew Brown"]
  spec.email       = ["andrew@exampro.co"]
  spec.license     = "MIT"

  spec.required_ruby_version = ">= 3.0"

  # All files tracked in git, plus the bin/ executable.
  spec.files = Dir["lib/**/*.rb"] + Dir["prompts/**/*.md"] + ["bin/boukensha"]

  spec.bindir      = "bin"
  spec.executables = ["boukensha"]

  # TUI libraries are optional runtime dependencies. Their published
  # Ruby-platform gems require locally compiled Go archives on native Windows,
  # while the plain REPL is dependency-free. Linux/WSL users who want the TUI
  # install bubbletea, lipgloss, and bubbles through the Gemfile.

  # open3, net/http, and json are stdlib. Users supply their own ANTHROPIC_API_KEY.
end
