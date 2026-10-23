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


CREATE TABLE IF NOT EXISTS dbd.sessions (
    session_id                  UUID NOT NULL PRIMARY KEY,
    group_id                    TEXT,
    session_start               TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end                 TIMESTAMP WITH TIME ZONE,
    ended_with_success          BOOLEAN,
    session_log                 JSONB
);

ALTER TABLE dbd.sessions OWNER TO dbd_owner;

COMMENT ON TABLE dbd.sessions IS 'Table to track sessions of deployments.';
COMMENT ON COLUMN dbd.sessions.session_id IS 'Unique identifier for the session.';
COMMENT ON COLUMN dbd.sessions.group_id IS 'Allows to identify the session by group it belongs to (e.g. "users db deployment").';
COMMENT ON COLUMN dbd.sessions.session_start IS 'Timestamp when the session started.';
COMMENT ON COLUMN dbd.sessions.session_end IS 'Timestamp when the session ended.';
COMMENT ON COLUMN dbd.sessions.ended_with_success IS 'Indicates whether the session ended successfully.';
COMMENT ON COLUMN dbd.sessions.session_log IS 'Log of the session in JSONB format.';

CREATE INDEX IF NOT EXISTS idx_sessions_group_id
    ON dbd.sessions (group_id, session_start DESC);
