#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import toml


class GlAuthBackends(object):
    """
    """

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module

        self.state = module.params.get("state")
        self.database_type = module.params.get("database_type")

    def run(self):
        """
          runner
        """
        result = dict(
            rc=0,
            failed=False,
            changed=False,
            msg="GlAuth Backends ..."
        )

        toml_data = toml.load("/etc/glauth/glauth.conf")
        glauth_backends = toml_data.get('backends')

        for backend in glauth_backends:
            if backend.get("datastore") == "plugin" and self.database_type in backend.get("plugin",
                                                                                          None):
                break

        if self.database_type == "sqlite":
            result = self._sqlite(backend)

        return result

    def _sqlite(self, config):
        """
        """
        import sqlite3

        database_file = config.get("database")

        _failed = False
        _changed = False
        _msg = ""

        if self.state == "create":
            """
            """
            conn = None

            try:
                conn = sqlite3.connect(
                    database_file,
                    isolation_level=None,
                    detect_types=sqlite3.PARSE_COLNAMES
                )
                conn.row_factory = lambda cursor, row: row[0]

                # self.module.log(msg=f"SQLite Version: '{sqlite3.version}'")

                query = "SELECT name FROM sqlite_schema WHERE type ='table' AND name not LIKE '%metadata%'"
                cursor = conn.execute(query)
                schemas = cursor.fetchall()
                # self.module.log(msg=f"  - schemas '{schemas}")
                if len(schemas) == 0:
                    """
                      import sql schema
                    """
                    # self.module.log(msg="import database schemas")

                    with open("/etc/glauth/databases/sqlite.sql", 'r') as f:
                        cursor.executescript(f.read())

                    _changed = True
                    _msg = "Database successfully created."
                else:
                    _msg = "Database already exists."

            except sqlite3.Error as er:
                self.module.log(msg=f"SQLite error: '{(' '.join(er.args))}'")
                self.module.log(msg=f"Exception class is '{er.__class__}'")

                _failed = True
                _msg = (' '.join(er.args))

            # exception sqlite3.Warning
            # # A subclass of Exception.
            #
            # exception sqlite3.Error
            # # The base class of the other exceptions in this module. It is a subclass of Exception.
            #
            # exception sqlite3.DatabaseError
            # # Exception raised for errors that are related to the database.
            #
            # exception sqlite3.IntegrityError
            # # Exception raised when the relational integrity of the database is affected, e.g. a foreign key check fails.
            # It is a subclass of DatabaseError.
            #
            # exception sqlite3.ProgrammingError
            # # Exception raised for programming errors, e.g. table not found or already exists, syntax error in the SQL statement,
            # wrong number of parameters specified, etc. It is a subclass of DatabaseError.
            #
            # exception sqlite3.OperationalError
            # # Exception raised for errors that are related to the database’s operation and not necessarily under the control of the programmer,
            # e.g. an unexpected disconnect occurs, the data source name is not found, a transaction could not be processed, etc.
            # It is a subclass of DatabaseError.
            #
            # exception sqlite3.NotSupportedError
            # # Exception raised in case a method or database API was used which is not supported by the database,
            # e.g. calling the rollback() method on a connection that does not support transaction or has transactions turned off.
            # It is a subclass of DatabaseError.

            finally:
                if conn:
                    conn.close()

            # conn = sqlite3.connect(
            #     database_file,
            #     isolation_level=None,
            #     detect_types=sqlite3.PARSE_COLNAMES
            # )

            return dict(
                rc=0,
                failed=_failed,
                changed=_changed,
                msg=_msg
            )

        elif self.state == "absent":
            """
            """
            pass

        return []


# ===========================================
# Module execution.
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                default="create",
                choices=["create", "delete"]
            ),
            database_type=dict(
                default="sqlite",
                choices=["sqlite", "mysql", "mariadb"]
            )
        ),
        supports_check_mode=False,
    )

    o = GlAuthBackends(module)
    result = o.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
