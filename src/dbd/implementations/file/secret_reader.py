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

import json
from pathlib import Path
from typing import Any

from dbd.abstract.abstract_secret_reader import AbstractSecretReader
from dbd.core.config import Config


class SecretReader(AbstractSecretReader):
    _data: dict[str, Any]

    def get_secret(self, secret_name: str) -> str | dict[str, Any] | list[Any] | None:
        result = self._data.get(secret_name)
        if result is None or isinstance(result, dict) or isinstance(result, list):
            return result

        return str(result)

    def __init__(self, config: Config):
        super().__init__(config)
        file_name = self.config.get_as_str("file_name")
        file_type = self.config.get_as_str("type", "json")
        file_path = Path(file_name)
        match file_type:
            case "json":
                with file_path.open(encoding="utf-8") as file:
                    data = json.load(file)
                    if not isinstance(data, dict):
                      raise ValueError(f"Secrets file must contain a JSON object: {file_path}")
                    self._data = data
            case _:
                raise ValueError(f"Unsupported file type: {file_type}")
