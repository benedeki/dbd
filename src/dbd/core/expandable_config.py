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

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dbd.core.simple_config import SimpleConfig

if TYPE_CHECKING:
    from dbd.abstract.abstract_secret_reader import AbstractSecretReader

class ExpandableConfig(SimpleConfig):
    def __init__(self,
                 config_file: str,
                 cli_parameters: dict[str, str]):
        """
        Loads a JSON configuration file and prepares it for expansion of placeholders for expansions
        :param config_file:    config_file is the path to the JSON configuration file to be loaded and expanded.
        :param cli_parameters: cli_parameters are provided to be used later for expansion of CLI references in the
                               config while remaining stable
        """
        config_file_path = Path(config_file)
        self._root = config_file_path.parent
        self._cli_parameters = cli_parameters
        loaded_data = self._load_file(config_file_path)
        if not isinstance(loaded_data, dict):
            raise ValueError(f"Configuration file must contain a JSON object: {config_file_path}")
        super().__init__(loaded_data)

    def expand(self, secret_reader: AbstractSecretReader | None = None, branch: str  = ""):
        data: dict[str, Any] = self.get_as_dict(branch) if branch else self._data
        self._expand_dict(data, secret_reader)

    def _expand_dict(self, data: dict, secret_reader: AbstractSecretReader | None) -> None:
        keys:list = list(data.keys())
        for key in keys:
            value = data[key]
            expanded_value = self._expand_value(value, secret_reader)
            if not isinstance(key, str):
                data.pop(key, None)
                data[str(key)] = expanded_value
            elif expanded_value != value:
                data[str(key)] = expanded_value

    def _expand_value(
        self,
        value: Any,
        secret_reader: AbstractSecretReader | None,
    ) -> Any:
        if isinstance(value, dict):
            self._expand_dict(value, secret_reader)
            return value
        if isinstance(value, list):
            return [self._expand_value(item, secret_reader) for item in value]
        if isinstance(value, str):
            match = REFERENCE_PATTERN.fullmatch(value)
            if match is None:
                return value
            reference_type: str = match.group("type")
            reference_value: str = match.group("value")
            match reference_type:
                case "FILE":
                    data = self._load_file(Path(reference_value))
                    return self._expand_value(data, secret_reader)
                case "SECRET":
                    if secret_reader is None:
                        raise ValueError(f"Secret reader is not provided for SECRET reference '{reference_value}'.")
                    secret = secret_reader.get_secret(reference_value)
                    return self._expand_value(secret, secret_reader)
                case "CLI":
                    cli_value = self._cli_parameters.get(reference_value)
                    if cli_value is None:
                        raise ValueError(f"CLI parameter '{reference_value}' has not been provided.")
                    return cli_value
                case "ENV":
                    env_value = os.getenv(reference_value)
                    if env_value is None:
                        raise ValueError(f"Environment variable '{reference_value}' is not set.")
                    return env_value
                case "CFG":
                    cfg_value = self.get(reference_value)
                    return self._expand_value(cfg_value, secret_reader)
                case _:
                    raise ValueError(f"Unknown reference type '{reference_type}'.")
        return value

    def _load_file(self, file_path: Path) -> Any:
        if not file_path.is_absolute():
            file_path = self._root / file_path
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
        return data

REFERENCE_PATTERN = re.compile(r"^__(?P<type>[A-Z]+)\((?P<value>.+)\)$")
