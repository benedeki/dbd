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

CREATE OR REPLACE FUNCTION dbd.version(
    OUT version_number  INTEGER
)RETURNS RECORD AS $$
-------------------------------------------------------------------------------
--
-- Function: dbd.version(0)
--      Returns the version of the `dbd` functions and the user who was granted access to them.
--
-- Parameters:
--      None
--
-- Returns:
--      version_number      - The version number of the function
--
-------------------------------------------------------------------------------
DECLARE
BEGIN
    version_number := {{VERSION_NUMBER}};

    RETURN;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

ALTER FUNCTION dbd.version() OWNER TO dbd_owner;
GRANT EXECUTE ON FUNCTION dbd.version() TO public;
