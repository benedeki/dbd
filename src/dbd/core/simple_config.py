# Copyright 2026 David Benedeki, All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import Any


class SimpleConfig:
    _data: dict[str, Any]

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str) -> Any:
        return self._data[key]

    def get_as_str(self, key: str, default: str | None = None) -> str:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if isinstance(value, list):
            result = "\n".join(str(x) for x in value)
            return result
        return str(value)

    def get_as_int(self, key: str, default: int | None = None) -> int:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        return int(value)

    def get_as_bool(self, key: str, default: bool | None = None) -> bool:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if isinstance(value, bool):
            return value
        lowered = str(value).strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"Cannot interpret '{value}' as boolean")

    def get_as_float(self, key: str, default: float | None = None) -> float:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        return float(value)

    def get_as_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if not isinstance(value, list):
            value = [value]
        return value

    def get_as_dict(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        value = self._data.get(key, default)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found.")
        if not isinstance(value, dict):
            raise ValueError(f"Configuration key '{key}' is not a dictionary.")
        return value

    def get_as_config(self, key: str, default: dict[str, Any] | None = None) -> SimpleConfig:
        return SimpleConfig(self.get_as_dict(key, default))
