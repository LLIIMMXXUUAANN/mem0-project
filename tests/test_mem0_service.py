import pytest

from mem0_service import Mem0Service, Mem0ServiceError, Memory


class FakeMemoryClient:
    def __init__(self):
        self.add_calls = []
        self.search_calls = []
        self.get_all_calls = []
        self.delete_calls = []
        self.search_response = {"results": []}
        self.get_all_response = {"results": []}
        self.raise_on = None

    def add(self, messages, user_id):
        if self.raise_on == "add":
            raise RuntimeError("boom")
        self.add_calls.append((messages, user_id))

    def search(self, query, filters, top_k):
        if self.raise_on == "search":
            raise RuntimeError("boom")
        self.search_calls.append((query, filters, top_k))
        return self.search_response

    def get_all(self, filters):
        if self.raise_on == "get_all":
            raise RuntimeError("boom")
        self.get_all_calls.append(filters)
        return self.get_all_response

    def delete(self, memory_id):
        if self.raise_on == "delete":
            raise RuntimeError("boom")
        self.delete_calls.append(memory_id)


def test_add_memory_calls_client_with_user_id():
    client = FakeMemoryClient()
    service = Mem0Service(client)
    messages = [{"role": "user", "content": "hi"}]

    service.add_memory("alice", messages)

    assert client.add_calls == [(messages, "alice")]


def test_add_memory_wraps_errors():
    client = FakeMemoryClient()
    client.raise_on = "add"
    service = Mem0Service(client)

    with pytest.raises(Mem0ServiceError):
        service.add_memory("alice", [{"role": "user", "content": "hi"}])


def test_search_memories_parses_results_dict():
    client = FakeMemoryClient()
    client.search_response = {
        "results": [{"id": "1", "memory": "Allergic to nuts", "score": 0.9}]
    }
    service = Mem0Service(client)

    result = service.search_memories("alice", "diet", limit=3)

    assert result == [Memory(id="1", text="Allergic to nuts")]
    assert client.search_calls == [("diet", {"user_id": "alice"}, 3)]


def test_search_memories_parses_bare_list():
    client = FakeMemoryClient()
    client.search_response = [{"id": "1", "memory": "Allergic to nuts"}]
    service = Mem0Service(client)

    result = service.search_memories("alice", "diet")

    assert result == [Memory(id="1", text="Allergic to nuts")]


def test_search_memories_wraps_errors():
    client = FakeMemoryClient()
    client.raise_on = "search"
    service = Mem0Service(client)

    with pytest.raises(Mem0ServiceError):
        service.search_memories("alice", "diet")


def test_search_memories_wraps_malformed_response():
    client = FakeMemoryClient()
    client.search_response = {"results": [{"id": "1"}]}  # missing "memory" key
    service = Mem0Service(client)

    with pytest.raises(Mem0ServiceError):
        service.search_memories("alice", "diet")


def test_get_all_memories_scopes_by_user():
    client = FakeMemoryClient()
    client.get_all_response = {"results": [{"id": "2", "memory": "Vegetarian"}]}
    service = Mem0Service(client)

    result = service.get_all_memories("alice")

    assert result == [Memory(id="2", text="Vegetarian")]
    assert client.get_all_calls == [{"user_id": "alice"}]


def test_get_all_memories_wraps_malformed_response():
    client = FakeMemoryClient()
    client.get_all_response = None  # not a dict or a list
    service = Mem0Service(client)

    with pytest.raises(Mem0ServiceError):
        service.get_all_memories("alice")


def test_delete_memory_calls_client():
    client = FakeMemoryClient()
    service = Mem0Service(client)

    service.delete_memory("2")

    assert client.delete_calls == ["2"]


def test_delete_memory_wraps_errors():
    client = FakeMemoryClient()
    client.raise_on = "delete"
    service = Mem0Service(client)

    with pytest.raises(Mem0ServiceError):
        service.delete_memory("2")
