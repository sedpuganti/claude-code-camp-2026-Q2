require_relative "helper"

class TestAnthropicBackend < Minitest::Test
  def test_system_prompt_uses_anthropic_content_blocks
    context = Boukensha::Context.new(
      task: Boukensha::Tasks::Player,
      system: "You are Boukensha."
    )
    backend = Boukensha::Backends::Anthropic.new(
      api_key: "test-key",
      model: "claude-haiku-4-5"
    )

    payload = backend.to_payload(context)

    assert_equal(
      [{ type: "text", text: "You are Boukensha." }],
      payload[:system]
    )
  end

  def test_nil_system_prompt_is_omitted
    context = Boukensha::Context.new(
      task: Boukensha::Tasks::Player,
      system: nil
    )
    backend = Boukensha::Backends::Anthropic.new(
      api_key: "test-key",
      model: "claude-haiku-4-5"
    )

    refute backend.to_payload(context).key?(:system)
  end
end
