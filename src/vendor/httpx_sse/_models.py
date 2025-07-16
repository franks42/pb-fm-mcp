import json
from typing import Any


class ServerSentEvent:
    def __init__(
        self,
        event: str | None = None,
        data: str | None = None,
        id: str | None = None,
        retry: int | None = None,
    ) -> None:
        if not event:
            event = "message"

        if data is None:
            data = ""

        if id is None:
            id = ""

        self._event = event
        self._data = data
        self._id = id
        self._retry = retry

    @property
    def event(self) -> str:
        return self._event

    @property
    def data(self) -> str:
        return self._data

    @property
    def id(self) -> str:
        return self._id

    @property
    def retry(self) -> int | None:
        return self._retry

    def json(self) -> Any:
        return json.loads(self.data)

    def __repr__(self) -> str:
        pieces = [f"event={self.event!r}"]
        if self.data != "":
            pieces.append(f"data={self.data!r}")
        if self.id != "":
            pieces.append(f"id={self.id!r}")
        if self.retry is not None:
            pieces.append(f"retry={self.retry!r}")
        return f"ServerSentEvent({', '.join(pieces)})"
