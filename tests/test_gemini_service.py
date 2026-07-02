import pytest

from gemini_service import (
    GeminiService,
    GeminiServiceError,
    build_contents,
    build_system_instruction,
)


def test_build_system_instruction_with_no_memories():
    result = build_system_instruction([])
    assert "(no known facts yet)" in result


def test_build_system_instruction_lists_memories():
    result = build_system_instruction(["Allergic to nuts", "Lives in Tokyo"])
    assert "- Allergic to nuts" in result
    assert "- Lives in Tokyo" in result


def test_build_contents_maps_assistant_role_to_model():
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]

    contents = build_contents(history, "how are you")

    assert [c.role for c in contents] == ["user", "model", "user"]
    assert contents[-1].parts[0].text == "how are you"


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self):
        self.calls = []
        self.raise_error = False

    def generate_content(self, model, contents, config):
        if self.raise_error:
            raise RuntimeError("boom")
        self.calls.append((model, contents, config))
        return FakeResponse("a reply")


class FakeGenaiClient:
    def __init__(self):
        self.models = FakeModels()


def test_generate_reply_returns_response_text():
    client = FakeGenaiClient()
    service = GeminiService(client, model="gemini-2.5-flash")

    reply = service.generate_reply("hi", ["Allergic to nuts"], [])

    assert reply == "a reply"
    model, contents, config = client.models.calls[0]
    assert model == "gemini-2.5-flash"
    assert "Allergic to nuts" in config.system_instruction


def test_generate_reply_wraps_errors():
    client = FakeGenaiClient()
    client.models.raise_error = True
    service = GeminiService(client)

    with pytest.raises(GeminiServiceError):
        service.generate_reply("hi", [], [])
