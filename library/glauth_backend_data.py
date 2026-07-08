#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Ansible module (backend implementation) to import GlAuth LDAP-emulation
group and user data into the SQLite backend database.

Reads ``groups`` and ``users`` dictionaries from the Ansible module
parameters and synchronizes them into the ``ldapgroups``,
``includegroups``, ``users`` and ``capabilities`` tables used by
GlAuth's SQLite plugin backend. A per-user checksum cache under
``~/.ansible/cache/glauth`` avoids unnecessary database writes when a
user's configuration has not changed.

(c) 2025-2026, Bodo Schulz <bodo@boone-schulz.de>
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import toml
from ansible.module_utils.basic import AnsibleModule

#: Standard Ansible module result dictionary (`failed`, `changed`, `msg`, ...).
ModuleResult = Dict[str, Any]

GLAUTH_CONFIG_FILE = "/etc/glauth/glauth.conf"

DOCUMENTATION = r"""
---
module: glauth_backend_data
short_description: Synchronize GlAuth LDAP group and user data into the SQLite backend
description:
  - Reads C(groups) and C(users) dictionaries from the module arguments
    and synchronizes them into the C(ldapgroups), C(includegroups),
    C(users) and C(capabilities) tables of the GlAuth SQLite plugin
    backend database.
  - The active database file is resolved from the C(plugin) backend
    entry matching C(database_type) in I(/etc/glauth/glauth.conf).
  - A per-user SHA-256 checksum is cached under
    I(~/.ansible/cache/glauth/<user>.checksum) on the target host, so
    unchanged users are skipped on subsequent runs.
  - Currently only C(database_type=sqlite) is fully implemented.
version_added: "1.0.0"
author:
  - Bodo Schulz (@bodsch)
options:
  database_type:
    description:
      - The GlAuth backend datastore type to write to. Must match a
        C(plugin) backend entry configured in
        I(/etc/glauth/glauth.conf).
    type: str
    choices: [sqlite, mysql, mariadb]
    default: sqlite
  groups:
    description:
      - Dictionary of LDAP group definitions, keyed by group name.
      - Each entry supports C(gid) (the group's numeric GID) and
        optionally C(include_groups), a list of GIDs of nested groups.
    type: dict
    required: false
    default: {}
  users:
    description:
      - Dictionary of LDAP user definitions, keyed by user (login) name.
      - Each entry supports C(uid), C(primary_group), C(other_groups),
        C(given_name), C(sn), C(mail), C(login_shell), C(home_dir),
        C(pass) (with C(sha256) / C(bcrypt) sub-keys), C(ssh_keys),
        C(otp_secret), C(yubikey) and C(capabilities).
      - See U(https://glauth.github.io/docs/databases.html) for the
        full field reference.
    type: dict
    required: false
    default: {}
notes:
  - Requires the C(toml) Python library on the target host.
  - This module writes directly to the SQLite database file via the
    C(sqlite3) standard library module; it does not go through GlAuth
    itself.
requirements:
  - python3
  - toml
"""

EXAMPLES = r"""
- name: Synchronize GlAuth groups and users into the SQLite backend
  glauth_backend_data:
    database_type: sqlite
    groups:
      superheros:
        gid: 5501
      superheros_readonly:
        gid: 5502
        include_groups:
          - 5501
    users:
      hackers:
        uid: 5001
        primary_group: 5501
        given_name: Leeroy
        sn: Jenkins
        mail: leeroy@example.com
        pass:
          sha256: "e4dc9b93326e5eb5673a730c07..."
        capabilities:
          search:
            object: "ou=superheros,dc=glauth,dc=com"
"""

RETURN = r"""
rc:
  description: Internal result code. C(0) on success, C(1) when no matching backend configuration was found.
  type: int
  returned: always
  sample: 0
failed:
  description: Whether the module execution failed, or whether any individual group/user synchronization failed.
  type: bool
  returned: always
  sample: false
changed:
  description: Whether any group or user was created, updated, or removed.
  type: bool
  returned: always
  sample: true
msg:
  description: >-
    On success, a dictionary mapping each processed user name to a
    human-readable per-user status message. On failure before user
    processing (e.g. missing schema), a plain error string instead.
  type: raw
  returned: always
  sample:
    hackers: "User successfully created."
    superman: "User has not changed."
"""


class GlAuthBackendData:
    """
    Synchronizes GlAuth LDAP group and user definitions into SQLite.

    Connects to the SQLite database referenced by the active GlAuth
    ``plugin`` backend configuration and upserts groups (and their
    nested ``includegroups``) as well as users (including passwords,
    SSH keys, OTP/YubiKey secrets and capabilities). A checksum file per
    user is used to skip unchanged entries.

    :param module: The active :class:`AnsibleModule` instance.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the instance from the Ansible module parameters.

        :param module: The active AnsibleModule instance.
        """
        self.module: AnsibleModule = module
        # self.module.log("GlAuthBackendData::__init__()")

        self.database_type: str = module.params.get("database_type")
        self.groups: Dict[str, Any] = module.params.get("groups") or {}
        self.users: Dict[str, Any] = module.params.get("users") or {}

        self.checksum_directory: str = str(Path.home() / ".ansible" / "cache" / "glauth")
        self.database_file: Optional[str] = None
        self._conn: Optional[sqlite3.Connection] = None

    def run(self) -> ModuleResult:
        """
        Locate the active SQLite backend and synchronize groups and users.

        :return: A dict with keys ``rc``, ``failed``, ``changed`` and
            ``msg``, matching the Ansible module result contract.
        """
        # self.module.log("GlAuthBackendData::run()")

        os.makedirs(self.checksum_directory, exist_ok=True)

        backend = self._find_plugin_backend()
        if backend is None:
            return dict(
                rc=1,
                failed=True,
                changed=False,
                msg=f"No '{self.database_type}' plugin backend configured in {GLAUTH_CONFIG_FILE}."
            )

        if self.database_type == "sqlite":
            return self._sqlite(backend)

        return dict(rc=0, failed=False, changed=False, msg="GlAuth Backend Data ...")

    def _find_plugin_backend(self) -> Optional[Dict[str, Any]]:
        """
        Read the GlAuth configuration and return the plugin-backed backend
        entry matching :attr:`database_type`, if any.

        :return: The matching backend dict, or ``None`` if none matched.
        """
        toml_data = toml.load(GLAUTH_CONFIG_FILE)
        glauth_backends: List[Dict[str, Any]] = toml_data.get("backends", [])

        for backend in glauth_backends:
            plugin = backend.get("plugin") or ""
            if backend.get("datastore") == "plugin" and self.database_type in plugin:
                return backend

        return None

    def _sqlite(self, config: Dict[str, Any]) -> ModuleResult:
        """
        Open the SQLite database and synchronize groups and users.

        :param config: The backend configuration dict (contains the
            ``database`` file path).
        :return: A dict with keys ``rc``, ``failed``, ``changed`` and
            ``msg``.
        """
        # self.module.log(f"GlAuthBackendData::_sqlite(config: {config})")

        self.database_file = config.get("database")
        result_state: List[Dict[str, Any]] = []
        failed = False
        msg: Any = ""

        try:
            self._conn = sqlite3.connect(
                self.database_file, isolation_level=None, detect_types=sqlite3.PARSE_COLNAMES
            )

            query = "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE '%metadata%'"
            schemas = self._conn.execute(query).fetchall()

            if len(schemas) == 0:
                failed = True
                msg = "Missing Database schemas."
            else:
                self.import_groups()
                result_state = self.import_users()

        except sqlite3.Error as error:
            failed = True
            self.module.log(msg=f"SQLite error: '{' '.join(error.args)}'")
            msg = " ".join(error.args)

        finally:
            if self._conn:
                self._conn.close()
                self._conn = None

        combined: Dict[str, Any] = {k: v for entry in result_state for k, v in entry.items()}
        changed = any(v.get("changed") for v in combined.values())
        failed = failed or any(v.get("failed") for v in combined.values())
        result_msg = {k: v.get("state") for k, v in combined.items()} or msg

        # self.module.log(msg=f" - changed '{changed}'")
        # self.module.log(msg=f" - failed  '{failed}'")

        return dict(rc=0, failed=failed, changed=changed, msg=result_msg)

    def import_groups(self) -> None:
        """
        Upsert all configured groups (and their ``include_groups``) into
        the ``ldapgroups`` / ``includegroups`` tables.

        Schema reference::

            CREATE TABLE IF NOT EXISTS ldapgroups (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              gidnumber INTEGER NOT NULL
            );
        """
        # self.module.log("GlAuthBackendData::import_groups()")

        for group, values in self.groups.items():
            gid = values.get("gid")
            include_groups = values.get("include_groups", [])

            exists, _error, existing_group_id, _msg = self.__check_database_value("ldapgroups", "name", group)

            if exists:
                success, _, _ = self.__execute_query(
                    "UPDATE ldapgroups SET gidnumber = ? WHERE name = ?", (gid, group)
                )
            else:
                success, last_inserted_id, _ = self.__execute_query(
                    "INSERT OR REPLACE INTO ldapgroups (`name`, `gidnumber`) VALUES (?, ?)", (group, gid)
                )
                existing_group_id = last_inserted_id

            if not success or not existing_group_id:
                continue

            self.__execute_query("DELETE FROM includegroups WHERE parentgroupid = ?", (existing_group_id,))

            for include_group in include_groups:
                # 'includegroupid' references the 'id' of another ldapgroups row.
                included_id = self.__group_id(int(include_group))
                if included_id:
                    self.__execute_query(
                        "INSERT INTO includegroups (`parentgroupid`, `includegroupid`) VALUES (?, ?)",
                        (existing_group_id, included_id)
                    )

    def import_users(self) -> List[Dict[str, Any]]:
        """
        Upsert all configured users into the ``users`` table, skipping
        users whose configuration checksum has not changed since the
        last run.

        Schema reference::

            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              uidnumber INTEGER NOT NULL,
              primarygroup INTEGER NOT NULL,
              othergroups TEXT DEFAULT '',
              givenname TEXT DEFAULT '',
              sn TEXT DEFAULT '',
              mail TEXT DEFAULT '',
              loginshell TEXT DEFAULT '',
              homedirectory TEXT DEFAULT '',
              disabled SMALLINT DEFAULT 0,
              passsha256 TEXT DEFAULT '',
              passbcrypt TEXT DEFAULT '',
              otpsecret TEXT DEFAULT '',
              sshkeys TEXT DEFAULT '',
              yubikey TEXT DEFAULT '',
              custattr TEXT DEFAULT '{}'
            );

        :return: A list of single-key dicts, one per processed user,
            mapping the user name to a ``{changed, failed, state}`` dict.
        """
        # self.module.log("GlAuthBackendData::import_users()")

        result_state: List[Dict[str, Any]] = []

        for user, values in self.users.items():
            checksum_file = os.path.join(self.checksum_directory, f"{user}.checksum")
            old_checksum = self.__read_checksum_file(checksum_file)
            current_checksum = self.__checksum(json.dumps(values, sort_keys=True))

            if old_checksum and old_checksum == current_checksum:
                result_state.append({user: dict(changed=False, failed=False, state="User has not changed.")})
                continue

            exists, _error, _id, _msg = self.__check_database_value("users", "name", user)

            if exists:
                success, _msg = self.__update_user(user, values)
                state = "User successfully updated."
            else:
                success, _msg = self.__insert_user(user, values)
                state = "User successfully created."

            # Fix: previously `_failed` was never set to True on failure (dead branch).
            result_state.append({user: dict(changed=True, failed=not success, state=state)})

            if success:
                self.__checksum_file(current_checksum, checksum_file)

        return result_state

    def __checksum(self, plaintext: str) -> str:
        """
        Compute the SHA-256 hex digest of a string.

        :param plaintext: The text to hash.
        :return: Hex-encoded SHA-256 digest.
        """
        return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()

    def __check_database_value(self, table: str, where: str, value: Any) -> Tuple[bool, bool, Optional[int], str]:
        """
        Check whether a row exists in ``table`` where ``where`` equals
        ``value``.

        :param table: Table name. Only ever called with hardcoded
            literals from this class — never with user-controlled input.
        :param where: Column name to filter on. Same constraint as
            ``table``.
        :param value: The (parameterized) value to look up.
        :return: Tuple of ``(exists, error, existing_id, msg)``.
        """
        # self.module.log(f"GlAuthBackendData::__check_database_value(table: {table}, where: {where}, value: {value})")

        try:
            query = f"SELECT id FROM {table} WHERE {where} = ?"
            row = self._conn.execute(query, (value,)).fetchone()

            if row is None:
                return False, False, None, f"The {where} does not exist."
            return True, False, row[0], f"{where} already created."

        except sqlite3.Error as error:
            self.module.log(msg=f"SQLite error: '{' '.join(error.args)}'")
            return False, True, None, " ".join(error.args)

    def __extract_user_fields(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a user configuration dict into a flat field mapping,
        applying the same defaults used by the GlAuth SQLite schema.

        Fix vs. legacy implementation: ``pass_sha256``/``pass_bcrypt``
        are now always defined (default ``None``), avoiding a
        ``NameError`` when ``values["pass"]`` is absent.

        :param values: The raw user configuration dict.
        :return: A dict of normalized fields.
        """
        passwords = values.get("pass") or {}

        return dict(
            given_name=values.get("given_name", ""),
            sn=values.get("sn", ""),
            mail=values.get("mail", ""),
            uid=values.get("uid"),
            primary_group=values.get("primary_group"),
            other_groups=values.get("other_groups", []),
            pass_sha256=passwords.get("sha256"),
            pass_bcrypt=passwords.get("bcrypt"),
            ssh_keys=values.get("ssh_keys", []),
            otp_secret=values.get("otp_secret"),
            yubikey=values.get("yubikey"),
            login_shell=values.get("login_shell", ""),
            home_dir=values.get("home_dir", ""),
            capabilities=values.get("capabilities", {}),
        )

    def __insert_user(self, user: str, values: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Insert a new user row and its dependent fields (groups,
        passwords, SSH keys, OTP/YubiKey secrets, capabilities).

        See: https://glauth.github.io/docs/databases.html

        :param user: The LDAP user (login) name.
        :param values: The user's configuration dict.
        :return: Tuple of ``(success, msg)``.
        """
        # self.module.log(f"GlAuthBackendData::__insert_user(user: {user})")
        fields = self.__extract_user_fields(values)

        success, last_inserted_id, msg = self.__execute_query(
            """
            INSERT INTO users
            (`name`, `uidnumber`, `primarygroup`, `givenname`, `sn`, `mail`, `loginshell`, `homedirectory`)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user, fields["uid"], fields["primary_group"], fields["given_name"],
             fields["sn"], fields["mail"], fields["login_shell"], fields["home_dir"])
        )

        if success and last_inserted_id:
            self.__apply_user_extras(fields["uid"], fields)

        return success, msg

    def __update_user(self, user: str, values: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing user row and its dependent fields.

        :param user: The LDAP user (login) name.
        :param values: The user's configuration dict.
        :return: Tuple of ``(success, msg)``.
        """
        # self.module.log(f"GlAuthBackendData::__update_user(user: {user})")
        fields = self.__extract_user_fields(values)

        success, _, msg = self.__execute_query(
            """
            UPDATE users SET
              `uidnumber` = ?, `primarygroup` = ?, `givenname` = ?, `sn` = ?,
              `mail` = ?, `loginshell` = ?, `homedirectory` = ?
            WHERE name = ?
            """,
            (fields["uid"], fields["primary_group"], fields["given_name"], fields["sn"],
             fields["mail"], fields["login_shell"], fields["home_dir"], user)
        )

        if success:
            self.__apply_user_extras(fields["uid"], fields)

        return success, msg

    def __apply_user_extras(self, uid: Any, fields: Dict[str, Any]) -> None:
        """
        Apply the secondary user fields (groups, passwords, SSH keys,
        OTP/YubiKey secrets, capabilities) not covered by the core
        ``INSERT``/``UPDATE`` statement.

        :param uid: The GlAuth ``uidnumber`` of the user.
        :param fields: The normalized field mapping from
            :meth:`__extract_user_fields`.
        """
        other_groups = fields["other_groups"]
        if other_groups and isinstance(other_groups, list):
            self.__update_user_single_field(uid, "othergroups", ",".join(map(str, other_groups)))

        if fields["pass_sha256"]:
            self.__update_user_single_field(uid, "passsha256", fields["pass_sha256"])

        if fields["pass_bcrypt"]:
            self.__update_user_single_field(uid, "passbcrypt", fields["pass_bcrypt"])

        if fields["otp_secret"]:
            self.__update_user_single_field(uid, "otpsecret", fields["otp_secret"])

        if fields["yubikey"]:
            self.__update_user_single_field(uid, "yubikey", fields["yubikey"])

        if fields["ssh_keys"]:
            self.__update_user_single_field(uid, "sshkeys", " ".join(fields["ssh_keys"]))

        if fields["capabilities"]:
            self.__update_user_capabilities(uid, fields["capabilities"])

    def __update_user_single_field(self, uid: Any, field: str, value: Any) -> None:
        """
        Update a single column of the ``users`` row identified by ``uid``.

        :param uid: The GlAuth ``uidnumber`` of the user.
        :param field: Column name to update. Only ever called with
            hardcoded literals — never user-controlled.
        :param value: The (parameterized) new value for the column.
        """
        # self.module.log(f"GlAuthBackendData::__update_user_single_field(uid: {uid}, field: {field})")
        self.__execute_query(f"UPDATE users SET {field} = ? WHERE uidnumber = ?", (value, uid))

    def __update_user_capabilities(self, uid: Any, capabilities: Dict[str, Any]) -> None:
        """
        Upsert the ``capabilities`` rows granted to a user.

        Schema reference::

            CREATE TABLE IF NOT EXISTS capabilities (
              id INTEGER PRIMARY KEY,
              userid INTEGER NOT NULL,
              action TEXT NOT NULL,
              object TEXT NOT NULL
            );

        :param uid: The GlAuth ``uidnumber`` of the user.
        :param capabilities: Mapping of ``action -> {"object": <scope>}``.
        """
        # self.module.log(f"GlAuthBackendData::__update_user_capabilities(uid: {uid})")

        for action, obj in capabilities.items():
            success, _, msg = self.__execute_query(
                "INSERT OR REPLACE INTO capabilities (`userid`, `action`, `object`) VALUES (?, ?, ?)",
                (uid, action, obj.get("object"))
            )
            if not success:
                self.module.log(msg=f"  ERROR : {msg}")
                break

    def __execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> Tuple[bool, Any, str]:
        """
        Execute a parameterized SQL statement against the open
        connection.

        Fix vs. legacy implementation: statements are now parameterized
        (``?`` placeholders) instead of interpolated via f-strings,
        eliminating SQL-injection risk. Also reuses the connection
        opened once in :meth:`_sqlite` instead of opening a new one per
        call.

        :param query: SQL statement with ``?`` placeholders.
        :param params: Values bound to the placeholders.
        :return: On success: ``(True, last_inserted_id_or_json_rows, "")``.
            For ``SELECT`` statements the second element is a
            JSON-encoded list of row dicts. On failure:
            ``(False, -1, error_message)``.
        """
        try:
            if query.strip().lower().startswith("select"):
                self._conn.row_factory = sqlite3.Row
                rows = [dict(row) for row in self._conn.execute(query, params).fetchall()]
                return True, json.dumps(rows), ""

            cursor = self._conn.execute(query, params)
            return True, cursor.lastrowid, "query successfully executed"

        except sqlite3.Error as error:
            self.module.log(msg="    ERROR")
            # self.module.log(msg=f"      query       : '{query}'")
            self.module.log(msg=f"      SQLite error: '{' '.join(error.args)}'")
            return False, -1, " ".join(error.args)
        finally:
            self._conn.row_factory = None

    def __group_id(self, gid: int) -> Optional[int]:
        """
        Resolve the internal ``ldapgroups.id`` for a given ``gidnumber``.

        :param gid: The GID number to look up.
        :return: The matching row id, or ``None`` if not found.
        """
        # self.module.log(f"GlAuthBackendData::__group_id(gid: {gid})")

        success, data = self.__group_data()
        if not success:
            return None

        rows = json.loads(data) if isinstance(data, str) else data
        matches = [row for row in rows if int(row.get("gidnumber")) == gid]
        return matches[0].get("id") if matches else None

    def __group_data(self) -> Tuple[bool, Any]:
        """
        Fetch all groups, ordered by GID.

        :return: Tuple of ``(success, json_rows)``.
        """
        # self.module.log("GlAuthBackendData::__group_data()")
        success, data, _ = self.__execute_query("SELECT id, name, gidnumber FROM ldapgroups ORDER BY gidnumber")
        return success, data

    def __checksum_file(self, checksum: str, checksum_file: str) -> bool:
        """
        Persist a checksum value to a file.

        :param checksum: The checksum string to write.
        :param checksum_file: Path of the file to write to.
        :return: ``True`` on success.
        """
        # self.module.log(f"GlAuthBackendData::__checksum_file(checksum_file: {checksum_file})")
        with open(checksum_file, "w") as handle:
            handle.write(checksum)
        return True

    def __read_checksum_file(self, checksum_file: str) -> Optional[str]:
        """
        Read a previously persisted checksum value, if present.

        :param checksum_file: Path of the checksum file.
        :return: The stored checksum, or ``None`` if the file does not
            exist.
        """
        # self.module.log(f"GlAuthBackendData::__read_checksum_file(checksum_file: {checksum_file})")
        if os.path.exists(checksum_file):
            with open(checksum_file, "r") as handle:
                return handle.readline().rstrip("\n") or None
        return None


def main() -> None:
    """
    Ansible module entry point.

    Defines the module argument specification, executes
    :class:`GlAuthBackendData`, and reports the result back to Ansible.
    """
    module = AnsibleModule(
        argument_spec=dict(
            database_type=dict(default="sqlite", choices=["sqlite", "mysql", "mariadb"]),
            groups=dict(type="dict", required=False, default={}),
            users=dict(type="dict", required=False, default={}),
        ),
        supports_check_mode=False,
    )

    handler = GlAuthBackendData(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
