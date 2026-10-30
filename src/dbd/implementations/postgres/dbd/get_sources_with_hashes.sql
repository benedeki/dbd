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

CREATE OR REPLACE FUNCTION dbd.get_sources_with_hashes(
    IN  i_group_id          TEXT,
    OUT source_name         TEXT,
    OUT source_hash         TEXT
)RETURNS SETOF RECORD AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.get_sources_with_hashes(0)
--      Returns all the sources deployed so far and their corresponding hashes for the given group_id.
--
-- Parameters:
--      i_group_id          - The group_id for which to retrieve the sources and their hashes
--
-- Returns:
--      source_name         - The name of the source
--      source_hash         - The hash of the source
--
-------------------------------------------------------------------------------
BEGIN
    RETURN QUERY
    SELECT
        S.source_name,
        S.source_hash
    FROM dbd.sources S
    WHERE S.group_id IS NOT DISTINCT FROM i_group_id;
END;
$$ LANGUAGE plpgsql VOLATILE SECURITY DEFINER;

ALTER FUNCTION dbd.get_sources_with_hashes(TEXT) OWNER TO dbd_owner;

GRANT EXECUTE ON FUNCTION dbd.get_sources_with_hashes(TEXT) TO dbd_user;
