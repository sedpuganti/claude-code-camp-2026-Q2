require_relative "helper"

class TestAnthropicBackend < Minitest::Test
  def test_system_prompt_is_an_array_of_text_blocks
    backend = Boukensha::Backends::Anthropic.new(
      api_key: "test-key",
      model: "claude-haiku-4-5"
    )
    context = Boukensha::Context.new(system: "Play the MUD.")

    payload = backend.to_payload(context, tools: [])

    assert_equal [{ type: "text", text: "Play the MUD." }], payload[:system]
  end

  def test_nil_system_prompt_is_omitted
    backend = Boukensha::Backends::Anthropic.new(
      api_key: "test-key",
      model: "claude-haiku-4-5"
    )
    context = Boukensha::Context.new(system: nil)

    refute backend.to_payload(context, tools: []).key?(:system)
  end
end
