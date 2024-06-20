from typing import Iterable

from textual.suggester import Suggester


class InputSuggester(Suggester):

    def __init__(
        self, suggestions: Iterable[str], *, case_sensitive: bool = True
    ) -> None:
        super().__init__(use_cache=False, case_sensitive=case_sensitive)
        self._suggestions = list(set(suggestions))
        self._for_comparison = (
            self._suggestions
            if self.case_sensitive
            else [suggestion.casefold() for suggestion in self._suggestions]
        )

    async def suggestions(self) -> list[str]:
        """TODO"""
        return list(set(self._suggestions))

    async def add_suggestion(self, value: str) -> None:
        """TODO"""
        if value not in self._suggestions:
            self._suggestions.append(value)
            self._for_comparison.append(value if self.case_sensitive else value.casefold())

    async def get_suggestion(self, value: str) -> str | None:
        """TODO"""
        for idx, suggestion in enumerate(self._for_comparison):
            if suggestion.startswith(value):
                return self._suggestions[idx]
        return None
