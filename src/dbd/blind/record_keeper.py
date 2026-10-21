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


from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.core.simple_config import SimpleConfig


class RecordKeeper(AbstractRecordKeeper):
    def start_session(self, full_config: SimpleConfig):
        pass

    def end_session(self, warnings: dict[str, str]):
        pass

    def get_source_hash(self, source_name: str) -> str | None:
        return None

    def record_deploy(self, source_name: str, source_hash: str):
        pass

    def source_checked(self, source_name: str):
        pass

