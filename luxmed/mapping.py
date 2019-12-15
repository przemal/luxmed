from collections.abc import Mapping
from typing import Any
from typing import Dict
from typing import Iterator

from luxmed.transport import LuxMedTransport


class LuxMedReadOnlyMapping(Mapping):
    def __init__(self, data: Dict, transport: LuxMedTransport):
        self.data = data
        self._transport = transport

    def __getitem__(self, item) -> Any:
        return self.data[item]

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator:
        return iter(self.data)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.data})'
