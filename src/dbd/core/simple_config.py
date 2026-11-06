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
    """Wrapper providing typed access to a configuration dictionary."""

    _data: dict[str, Any]

    def __init__(self, data: dict[str, Any]):
        """Initialize a configuration wrapper.

        :param data: Configuration values.
        :return: None.
        """
        self._data = data

    def __contains__(self, key: str) -> bool:
        """Check whether a configuration key exists.

        :param key: Key to look up.
        :return: ``True`` if the key exists, otherwise ``False``.
        """
        return key in self._data

    def get(self, key: str) -> Any:
        """Return a raw configuration value.

        :param key: Key to look up.
        :return: The value, or ``None`` if the key is absent.
        """
        return self._data.get(key)

    def get_as_str_optional(self, key: str) -> str | None:
        """Return a value as a string when present.

        :param key: Key to look up.
        :return: A string representation, or ``None`` if the key is absent.
        """
        value = self.get(key)
        if value is None:
            return None
        if isinstance(value, list):
            result = "\n".join(str(x) for x in value)
            return result
        return str(value)

    def get_as_str(self, key: str, default: str | None = None) -> str:
        """Return a required or defaulted string value.

        :param key: Key to look up.
        :param default: Value to return when the key is absent.
        :return: The value converted to a string.
        :raises KeyError: If the key is absent and no default is provided.
        """
        value = self.get_as_str_optional(key)
        if value is None:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key}' not found.")
        return str(value)

    def get_as_int(self, key: str, default: int | None = None) -> int:
        """Return a required or defaulted integer value.

        :param key: Key to look up.
        :param default: Value to return when the key is absent.
        :return: The value converted to an integer.
        :raises KeyError: If the key is absent and no default is provided.
        """
        value = self.get(key)
        if value is None:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key}' not found.")
        return int(value)

    def get_as_bool(self, key: str, default: bool | None = None) -> bool:
        """Return a required or defaulted boolean value.

        :param key: Key to look up.
        :param default: Value to return when the key is absent.
        :return: The normalized boolean value.
        :raises KeyError: If the key is absent and no default is provided.
        :raises ValueError: If the value cannot be interpreted as a boolean.
        """
        value = self.get(key)
        if value is None:
            if default is not None:
                return default
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
        """Return a required or defaulted floating-point value.

        :param key: Key to look up.
        :param default: Value to return when the key is absent.
        :return: The value converted to a float.
        :raises KeyError: If the key is absent and no default is provided.
        """
        value = self.get(key)
        if value is None:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key}' not found.")
        return float(value)

    def get_as_list(self, key: str, default: list[Any] | None = None) -> list[Any]:
        """Return a value as a list.

        :param key: Key to look up.
        :param default: Value to return when the key is absent.
        :return: The existing list or a single value wrapped in a list.
        :raises KeyError: If the key is absent and no default is provided.
        """
        value = self.get(key)
        if value is None:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key}' not found.")
        if not isinstance(value, list):
            value = [value]
        return value

    def get_as_dict(self, key: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return a configuration value as a dictionary.

        :param key: Key to look up.
        :param default: Value to return when the key is absent.
        :return: The configuration dictionary.
        :raises KeyError: If the key is absent and no default is provided.
        :raises ValueError: If the value is not a dictionary.
        """
        value = self.get(key)
        if value is None:
            if default is not None:
                return default
            raise KeyError(f"Configuration key '{key}' not found.")
        if not isinstance(value, dict):
            raise ValueError(f"Configuration key '{key}' is not a dictionary.")
        return value

    def get_as_config(self, key: str, default: dict[str, Any] | None = None) -> SimpleConfig:
        """Return a nested configuration wrapper.

        :param key: Key containing the nested configuration.
        :param default: Dictionary to wrap when the key is absent.
        :return: A configuration wrapper around the nested dictionary.
        :raises KeyError: If the key is absent and no default is provided.
        :raises ValueError: If the value is not a dictionary.
        """
        return SimpleConfig(self.get_as_dict(key, default))
