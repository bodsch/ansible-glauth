#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Ansible module (backend implementation) to create or remove the GlAuth
SQLite backend database.

Reads the active GlAuth backend configuration from
``/etc/glauth/glauth.conf`` and, for the ``sqlite`` backend, creates the
database schema (state=create) or removes the database file
(state=absent).

(c) 2025-2026, Bodo Schulz <bodo@boone-schulz.de>
"""

from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, List, Optional

import toml
from ansible.module_utils.basic import AnsibleModule

#: Standard Ansible module result dictionary (`failed`, `changed`, `msg`, ...).
ModuleResult = Dict[str, Any]

GLAUTH_CONFIG_FILE = "/etc/glauth/glauth.conf"
GLAUTH_SQLITE_SCHEMA = "/etc/glauth/databases/sqlite.sql"

DOCUMENTATION = r"""
---
module: glauth_backend
short_description: Manage the GlAuth SQLite backend database lifecycle
description:
  - Reads the C(backends) section of the GlAuth TOML configuration file
    (I(/etc/glauth/glauth.conf)) to locate the active plugin-backed
    database backend.
  - For the C(sqlite) database type, creates the database schema from
    I(/etc/glauth/databases/sqlite.sql) when C(state=create), or removes
    the database file when C(state=absent).
  - Currently only C(database_type=sqlite) is fully implemented;
    C(mysql) and C(mariadb) are accepted as valid choices but perform no
    action.
version_added: "1.0.0"
author:
  - Bodo Schulz (@bodsch)
options:
  state:
    description:
      - Whether the backend database should be present (created) or
        absent (removed).
    type: str
    choices: [create, absent]
    default: create
  database_type:
    description:
      - The GlAuth backend datastore type to manage. Must match a
        C(plugin) backend entry configured in
        I(/etc/glauth/glauth.conf).
    type: str
    choices: [sqlite, mysql, mariadb]
    default: sqlite
notes:
  - This module is not idempotency-transparent for C(mysql) / C(mariadb)
    - it currently returns C(changed=false) without performing any
      action for those database types.
  - Requires the C(toml) Python library on the target host.
requirements:
  - python3
  - toml
"""

EXAMPLES = r"""
- name: Create the GlAuth SQLite backend database
  glauth_backend:
    state: create
    database_type: sqlite

- name: Remove the GlAuth SQLite backend database
  glauth_backend:
    state: absent
    database_type: sqlite
"""

RETURN = r"""
rc:
  description: Internal result code. C(0) on success, C(1) when no matching backend configuration was found.
  type: int
  returned: always
  sample: 0
failed:
  description: Whether the module execution failed.
  type: bool
  returned: always
  sample: false
changed:
  description: Whether the database was created or removed by this run.
  type: bool
  returned: always
  sample: true
msg:
  description: Human-readable result message.
  type: str
  returned: always
  sample: "Database successfully created."
"""


class GlAuthBackends:
    """
    Manages the lifecycle of the GlAuth SQLite backend database.

    Reads the ``backends`` section of the GlAuth TOML configuration to
    locate the active plugin-backed database, then creates
    (state=create) or removes (state=absent) it as requested.

    :param module: The active :class:`AnsibleModule` instance.
    """

    def __init__(self, module: AnsibleModule) -> None:
        """
        Initialize the instance from the Ansible module parameters.

        :param module: The active AnsibleModule instance.
        """
        self.module: AnsibleModule = module
        # self.module.log("GlAuthBackends::__init__()")

        self.state: str = module.params.get("state")
        self.database_type: str = module.params.get("database_type")

    def run(self) -> ModuleResult:
        """
        Locate the active backend configuration and dispatch to the
        handler matching :attr:`database_type`.

        :return: A dict with keys ``rc``, ``failed``, ``changed`` and
            ``msg``, matching the Ansible module result contract.
        """
        # self.module.log("GlAuthBackends::run()")

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

        return dict(rc=0, failed=False, changed=False, msg="GlAuth Backends ...")

    def _find_plugin_backend(self) -> Optional[Dict[str, Any]]:
        """
        Read the GlAuth configuration and return the plugin-backed backend
        entry matching :attr:`database_type`, if any.

        Fix vs. legacy implementation: previously, if no backend matched,
        the loop variable silently retained the *last* list entry (or
        raised ``UnboundLocalError`` on an empty list), causing the wrong
        backend config to be used downstream.

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
        Create or remove the SQLite database file for the given backend
        configuration, depending on :attr:`state`.

        :param config: The backend configuration dict (contains the
            ``database`` file path).
        :return: A dict with keys ``failed``, ``changed`` and ``msg``.
        """
        # self.module.log(f"GlAuthBackends::_sqlite(config: {config})")
        database_file: str = config.get("database")

        if self.state == "create":
            return self._sqlite_create(database_file)
        if self.state == "absent":
            return self._sqlite_remove(database_file)

        return dict(failed=True, changed=False, msg=f"Unsupported state '{self.state}'.")

    def _sqlite_create(self, database_file: str) -> ModuleResult:
        """
        Create the SQLite database schema if the database is empty.

        :param database_file: Path to the SQLite database file.
        :return: A dict with keys ``failed``, ``changed`` and ``msg``.
        """
        failed = False
        changed = False
        msg = ""
        conn: Optional[sqlite3.Connection] = None

        try:
            conn = sqlite3.connect(
                database_file, isolation_level=None, detect_types=sqlite3.PARSE_COLNAMES
            )
            conn.row_factory = lambda cursor, row: row[0]

            query = "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE '%metadata%'"
            cursor = conn.execute(query)
            schemas = cursor.fetchall()

            if len(schemas) == 0:
                with open(GLAUTH_SQLITE_SCHEMA, "r") as schema_file:
                    cursor.executescript(schema_file.read())
                changed = True
                msg = "Database successfully created."
            else:
                msg = "Database already exists."

        except sqlite3.Error as error:
            self.module.log(msg=f"SQLite error: '{' '.join(error.args)}'")
            failed = True
            msg = " ".join(error.args)

        finally:
            if conn:
                conn.close()

        return dict(failed=failed, changed=changed, msg=msg)

    def _sqlite_remove(self, database_file: str) -> ModuleResult:
        """
        Remove the SQLite database file, if present.

        This implements the previously dead ``absent``/``delete`` state,
        which in the legacy code fell through to ``return []`` and would
        have crashed ``module.exit_json(**result)``.

        :param database_file: Path to the SQLite database file.
        :return: A dict with keys ``failed``, ``changed`` and ``msg``.
        """
        if not database_file or not os.path.exists(database_file):
            return dict(failed=False, changed=False, msg="Database does not exist.")

        try:
            os.remove(database_file)
            return dict(failed=False, changed=True, msg="Database successfully removed.")
        except OSError as error:
            return dict(failed=True, changed=False, msg=f"Database could not be removed: {error}")


def main() -> None:
    """
    Ansible module entry point.

    Defines the module argument specification, executes
    :class:`GlAuthBackends`, and reports the result back to Ansible.
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="create", choices=["create", "absent"]),
            database_type=dict(default="sqlite", choices=["sqlite", "mysql", "mariadb"])
        ),
        supports_check_mode=False,
    )

    handler = GlAuthBackends(module)
    result = handler.run()

    module.log(msg=f"= result: {result}")
    module.exit_json(**result)


if __name__ == "__main__":
    main()
