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

CREATE OR REPLACE FUNCTION dbd.new_session(
    IN  i_group_id        TEXT,
    OUT id_session        UUID,
)RETURNS UUID AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.new_session(0)
--      Starts a new deployment session for the specified group ID.
--
-- Parameters:
--      i_group_id        - The group ID for which to create a new session
--
-- Returns:
--      id_session        - The ID of the newly created session
--
-------------------------------------------------------------------------------
DECLARE
    _id_session UUID;
BEGIN
    _id_session := uuidv7();

    INSERT INTO dbd.sessions (
        id_session,
        group_id,
        session_start
    ) VALUES (
        _id_session,
        i_group_id,
        clock_timestamp()
    );

    id_session := _id_session;
    RETURN;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

ALTER FUNCTION dbd.new_session(TEXT) OWNER TO dbd_owner;
