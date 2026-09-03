from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DatasetEntry:
    id: int | None = None
    source_language: str = "hi"
    target_language: str = "sat"
    domain: str = "general"
    source_text: str = ""
    target_text: str = ""
    validated: bool = False
    created_at: str = ""
    updated_at: str = ""


class InMemoryDatasetStore:
    def __init__(self) -> None:
        self.entries: list[DatasetEntry] = []
        self._next_id = 1

    def add_entry(self, entry: DatasetEntry) -> DatasetEntry:
        entry.id = self._next_id
        self._next_id += 1
        entry.created_at = entry.created_at or "2026-09-02T00:00:00Z"
        entry.updated_at = entry.updated_at or entry.created_at
        self.entries.append(entry)
        return entry

    def list_entries(self) -> list[DatasetEntry]:
        return list(self.entries)

    def stats(self) -> dict[str, Any]:
        by_language: dict[str, int] = {}
        for entry in self.entries:
            by_language[entry.target_language] = by_language.get(entry.target_language, 0) + 1
        return {
            "total_entries": len(self.entries),
            "validated_entries": sum(1 for entry in self.entries if entry.validated),
            "by_language": by_language,
        }


dataset_store = InMemoryDatasetStore()
