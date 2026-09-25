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
from typing import Any

import boto3

from dbd.abstract.abstract_secret_reader import AbstractSecretReader
from dbd.core.config import Config


class SecretReader(AbstractSecretReader):
    """Secret reader backed by AWS Secrets Manager."""
    region_name: str
    client: Any

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.region_name = config.get("region_name")
        self.client = boto3.client("secretsmanager", region_name=self.region_name)

    def get_secret(self, secret_name: str) -> str | dict[str, Any] | None:
        response = self.client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString")
        if secret_string is None:
            return None
        raw = json.loads(secret_string)
        if not isinstance(raw, dict):
            return str(secret_string)
        data: dict[str, Any] = raw
        return data
