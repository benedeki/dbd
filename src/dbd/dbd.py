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

import sys
from enum import Enum

from dbd.abstract.abstract_destination_system import AbstractDestinationSystem
from dbd.abstract.abstract_record_keeper import AbstractRecordKeeper
from dbd.abstract.abstract_source_provider import AbstractSourceProvider
from dbd.core.config import Config
from dbd.core.driver import Driver


class Action(Enum):
    INSTALL = "install"

def _load_parameters() -> tuple[Action, Config]:
    action = Action(sys.argv[1])
    config = Config.from_file(sys.argv[2])
    return action, config

def _load_classes(config: Config) -> tuple[AbstractRecordKeeper, AbstractSourceProvider, AbstractDestinationSystem]:
    raise NotImplementedError

def main():
    action, config = _load_parameters()
    record_keeper, source_provider, destination_system = _load_classes(config)
    config.expand()
    driver = Driver(config, record_keeper, source_provider, destination_system)
    match action:
        case Action.INSTALL:
            driver.install()
        case _:
            raise NotImplementedError


if __name__ == '__main__':
    main()
