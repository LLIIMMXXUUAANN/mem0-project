"""Thin wrapper around the Mem0 Cloud MemoryClient."""
from dataclasses import dataclass
from typing import Any


class Mem0ServiceError(Exception):
    """Raised when a Mem0 Cloud API call fails."""


@dataclass
class Memory:
    id: str
    text: str


class Mem0Service:
    def __init__(self, client: Any):
        self._client = client

    def add_memory(self, user_id: str, messages: list[dict[str, str]]) -> None:
        try:
            self._client.add(messages=messages, user_id=user_id)
        except Exception as exc:
            raise Mem0ServiceError(f"Failed to save memory: {exc}") from exc

    def search_memories(self, user_id: str, query: str, limit: int = 5) -> list[Memory]:
        try:
            response = self._client.search(
                query=query, filters={"user_id": user_id}, top_k=limit
            )
            return _parse_memories(response)
        except Exception as exc:
            raise Mem0ServiceError(f"Failed to search memories: {exc}") from exc

    def get_all_memories(self, user_id: str) -> list[Memory]:
        try:
            response = self._client.get_all(filters={"user_id": user_id})
            return _parse_memories(response)
        except Exception as exc:
            raise Mem0ServiceError(f"Failed to list memories: {exc}") from exc

    def delete_memory(self, memory_id: str) -> None:
        try:
            self._client.delete(memory_id=memory_id)
        except Exception as exc:
            raise Mem0ServiceError(f"Failed to delete memory: {exc}") from exc


def _parse_memories(response: Any) -> list[Memory]:
    # mem0's SDK has been observed returning both a bare list and a
    # {"results": [...]} dict depending on version; handle both.
    items = response.get("results", []) if isinstance(response, dict) else response
    return [Memory(id=item["id"], text=item["memory"]) for item in items]
