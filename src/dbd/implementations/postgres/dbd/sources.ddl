/*
 * Copyright 2026 David Benedeki, All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


CREATE TABLE IF NOT EXISTS dbd.sources (
    group_id                        TEXT
        COMMENT 'Group identifier for the source.',
    source_name                     TEXT NOT NULL PRIMARY KEY
        COMMENT 'Name of the source.',
    source_hash                     TEXT NOT NULL
        COMMENT 'Hash of the source content.',
    key_session_of_first_deployment UUID NOT NULL
        COMMENT 'Identifier of the session that first deployed this source.',
    key_session_of_last_deployment  UUID
        COMMENT 'Identifier of the session that last deployed this source.',
    key_session_of_last_check      UUID
        COMMENT 'Identifier of the session that last checked this source, no necessary deploy.',
    last_deployed_at                 TIMESTAMP WITH TIME ZONE
        COMMENT 'Timestamp of the last deployment of this source.',
    last_check_at                 TIMESTAMP WITH TIME ZONE
        COMMENT 'Timestamp of the last time this source was checked, no necessary deploy.',
    PRIMARY KEY (group_id, source_name) NULLS NOT DISTINCT
);

ALTER TABLE SET OWNER dbd.sources TO ROLE dbd_owner;
COMMENT ON TABLE dbd.sources IS 'Table to track deployment of sources.';

CREATE INDEX IF NOT EXISTS idx_sources_group_id_source_name
    ON dbd.sources (group_id, source_name);

