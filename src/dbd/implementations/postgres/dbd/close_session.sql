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

CREATE OR REPLACE FUNCTION dbd.close_session(
    IN  i_session_id            UUID,
    IN  i_ended_with_success    BOOLEAN,
    IN  i_session_log           JSONB,
    OUT group_id                TEXT,
    OUT session_start           TIMESTAMP WITH TIME ZONE,
    OUT session_end             TIMESTAMP WITH TIME ZONE
)RETURNS RECORD AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.close_session(3)
--      Closes the specified deployment session and records whether it ended successfully.
--
-- Parameters:
--      i_session_id            - The ID of the session to close
--      i_ended_with_success    - Whether the session ended successfully
--      i_session_log           - The log of the session in JSONB format
--
-- Returns:
--      group_id            - The ID of the group associated with the session
--      session_start       - The start time of the session
--      session_end         - The end time of the session
--
-------------------------------------------------------------------------------
DECLARE
BEGIN
    IF i_ended_with_success IS NULL THEN
       RAISE EXCEPTION 'i_ended_with_success cannot be NULL';
    END IF;

    UPDATE dbd.sessions S
    SET session_end = clock_timestamp(),
        ended_with_success = i_ended_with_success,
        session_log = i_session_log
    WHERE S.session_id = i_session_id AND
          S.session_end IS NULL
    RETURNING S.group_id, S.session_start, S.session_end
    INTO group_id, session_start, session_end;

    IF NOT found THEN
        RAISE EXCEPTION 'No open session found with session_id: %', i_session_id;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql VOLATILE SECURITY DEFINER;

ALTER FUNCTION dbd.close_session(UUID, BOOLEAN, JSONB) OWNER TO dbd_owner;

GRANT EXECUTE ON FUNCTION dbd.close_session(UUID, BOOLEAN, JSONB) TO dbd_user;
