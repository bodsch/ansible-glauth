#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

import os
import json
import toml

from pathlib import Path


class GlAuthBackendData(object):
    """
    """

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module

        self.database_type = module.params.get("database_type")
        self.groups = module.params.get("groups")
        self.users = module.params.get("users")

        self.checksum_directory = f"{Path.home()}/.ansible/cache/glauth"

    def run(self):
        """
          runner
        """
        result_state = []

        result = dict(
            rc=0,
            failed=False,
            changed=False,
            msg="GlAuth Backend Data ..."
        )

        self.__create_directory(self.checksum_directory)

        toml_data = toml.load("/etc/glauth/glauth.conf")
        glauth_backends = toml_data.get('backends')

        self.module.log(msg=f"  - '{glauth_backends}'")

        for backend in glauth_backends:
            if backend.get("datastore") == "plugin" and self.database_type in backend.get("plugin", None):
                break

        self.module.log(msg=f"  - '{backend}")

        if self.database_type == "sqlite":
            result = self._sqlite(backend)

        return result


    def _sqlite(self, config):
        """
        """
        import sqlite3

        self.database_file = config.get("database")

        _failed = False
        _changed = False
        _msg = ""
        result_state = []

        conn = None

        try:
          conn = sqlite3.connect(
              self.database_file,
              isolation_level=None,
              detect_types=sqlite3.PARSE_COLNAMES
          )
          conn.row_factory = lambda cursor, row: row[0]

          schemas = []
          query = "SELECT name FROM sqlite_schema WHERE type ='table' AND name not LIKE '%metadata%'"

          cursor = conn.execute(query)

          schemas = cursor.fetchall()

          if len(schemas) == 0:
              _failed = True
              _msg = "Missing Database schemas."
          else:
              """
              """
              self.import_groups()

              result_state = self.import_users()


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
        # # Exception raised when the relational integrity of the database is affected, e.g. a foreign key check fails. It is a subclass of DatabaseError.
        #
        # exception sqlite3.ProgrammingError
        # # Exception raised for programming errors, e.g. table not found or already exists, syntax error in the SQL statement, wrong number of parameters specified, etc. It is a subclass of DatabaseError.
        #
        # exception sqlite3.OperationalError
        # # Exception raised for errors that are related to the database’s operation and not necessarily under the control of the programmer, e.g. an unexpected disconnect occurs, the data source name is not found, a transaction could not be processed, etc. It is a subclass of DatabaseError.
        #
        # exception sqlite3.NotSupportedError
        # # Exception raised in case a method or database API was used which is not supported by the database, e.g. calling the rollback() method on a connection that does not support transaction or has transactions turned off. It is a subclass of DatabaseError.

        finally:
            if conn:
                conn.close()

        self.module.log(msg=f" - '{result_state}'")

        # define changed for the running tasks
        # migrate a list of dict into dict
        combined_d = {key: value for d in result_state for key, value in d.items()}

        # find all changed and define our variable
        changed = (len({k: v for k, v in combined_d.items() if v.get('changed')}) > 0)
        # find all failed and define our variable
        failed = (len({k: v for k, v in combined_d.items() if v.get('failed')}) > 0)

        result_msg = {k: v.get('state') for k, v in combined_d.items()}

        return dict(
            rc=0,
            failed=failed,
            changed=changed,
            msg=result_msg
        )


    def import_groups(self):
        """
        """
        # import sqlite3

        self.module.log(msg=f"groups: {self.groups}'")

        for group, values in self.groups.items():
            self.module.log(msg=f"  - group: {group}'")

            include_groups = values.get("include_groups", [])

            # CREATE TABLE IF NOT EXISTS groups (
            #   id INTEGER PRIMARY KEY,
            #   name TEXT NOT NULL,
            #   gidnumber INTEGER NOT NULL
            # );
            query = f"insert or replace into groups (`name`, `gidnumber`) values ('{group}', '{values.get('gid')}')"
            self.module.log(msg=f"  - query: {query}'")

            result, last_inserted_id, msg = self.__execute_query(query)

            if result:
                if len(include_groups) > 0 and last_inserted_id:
                    # CREATE TABLE IF NOT EXISTS includegroups (
                    #   id INTEGER PRIMARY KEY,
                    #   parentgroupid INTEGER NOT NULL,
                    #   includegroupid INTEGER NOT NULL
                    # );
                    for include_group in include_groups:
                        """
                        """
                        query = f"insert or replace into includegroups (`parentgroupid`, `includegroupid`) values('{last_inserted_id}', '{include_group}')"
                        self.module.log(msg=f"  - query: {query}'")

                        result, last_inserted_id, msg = self.__execute_query(query)

        pass


    def import_users(self):
        """
        """
        # import sqlite3

        self.module.log(msg=f"users: {self.users}'")

        result_state = []

        # CREATE TABLE IF NOT EXISTS users (
        #   id INTEGER PRIMARY KEY,
        #   name TEXT NOT NULL,
        #   uidnumber INTEGER NOT NULL,
        #   primarygroup INTEGER NOT NULL,
        #   othergroups TEXT DEFAULT '',
        #   givenname TEXT DEFAULT '',
        #   sn TEXT DEFAULT '',
        #   mail TEXT DEFAULT '',
        #   loginshell TYEXT DEFAULT '',
        #   homedirectory TEXT DEFAULT '',
        #   disabled SMALLINT  DEFAULT 0,
        #   passsha256 TEXT DEFAULT '',
        #   passbcrypt TEXT DEFAULT '',
        #   otpsecret TEXT DEFAULT '',
        #   sshkeys TEXT DEFAULT '',
        #   yubikey TEXT DEFAULT '',
        #   custattr TEXT DEFAULT '{}'
        # );

        for user, values in self.users.items():
            self.module.log(msg=f"  - user: {user}'")

            res = {}

            _checksum_file = os.path.join(self.checksum_directory, f"{user}.checksum")

            old_checksum = self.__read_checksum_file(_checksum_file)
            cur_checksum = self.__checksum(json.dumps(values, sort_keys=True))

            self.module.log(msg=f"  - old_checksum : '{old_checksum}'")
            self.module.log(msg=f"  - cur_checksum : '{cur_checksum}'")

            if old_checksum and old_checksum == cur_checksum:

                res[user] = dict(
                    changed=False,
                    state="User has not schanged."
                )
            else:
                # first step:
                # take a lock into the database
                user_exists, error, existing_userid, error_message = self.__list_user(user)

                if user_exists:
                    """
                      update
                    """
                    self.__update_user(user, values)

                    res[user] = dict(
                        changed=True,
                        state="User successfully updated."
                    )

                else:
                    """
                      insert
                    """
                    self.__insert_user(user, values)

                    res[user] = dict(
                        changed=True,
                        state="User successfully created."
                    )

            result_state.append(res)

            self.__checksum_file(cur_checksum, _checksum_file)

        return result_state


    def __password_hash(self, plaintext):
        """
          https://docs.python.org/3/library/crypt.html
        """
        # self.module.log(msg="- __password_hash({})".format(plaintext))

        import crypt
        salt = ""
        try:
            salt = crypt.mksalt(crypt.METHOD_SHA512)
        except Exception as e:
            import random
            CHARACTERS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            salt = ''.join(random.choice(CHARACTERS) for i in range(16))
            # Use SHA512
            # return '$6$' + salt

        return crypt.crypt(
            plaintext,
            salt
        )


    def __checksum(self, plaintext):
        """
        """
        # self.module.log(msg="- __checksum({})".format(plaintext))

        import hashlib
        password_bytes = plaintext.encode('utf-8')
        password_hash = hashlib.sha256(password_bytes)
        return password_hash.hexdigest()


    def __list_user(self, user):
        """
        """
        import sqlite3

        existing_user = 0

        try:
          conn = sqlite3.connect(
              self.database_file,
              isolation_level=None,
              detect_types=sqlite3.PARSE_COLNAMES
          )
          conn.row_factory = lambda cursor, row: row[0]

          query = f"select id from users where name = '{user}'"

          cursor = conn.execute(query)

          existing_user = cursor.fetchall()

          if isinstance(existing_user, list) and len(existing_user) > 0:
              existing_user = existing_user[0]

          if existing_user == 0:
              _exists = False
              _error = False
              _msg = "The user does not exist."
          else:
              _exists = True
              _error = False
              _msg = "User already created."

        except sqlite3.Error as er:
            self.module.log(msg=f"SQLite error: '{(' '.join(er.args))}'")
            self.module.log(msg=f"Exception class is '{er.__class__}'")

            _exists = False
            _error = True
            _msg = (' '.join(er.args))

        return _exists, _error, existing_user, _msg


        # try:
        #     number_of_rows = cursor.execute(q)
        #     cursor.fetchone()
        #     cursor.close()
        #
        # except Exception as e:
        #     self.module.fail_json(msg="Cannot execute SQL '%s' : %s" % (q, to_native(e)))
        #
        # if number_of_rows == 1:
        #     return True, False, ""
        # else:
        #     return False, False, ""


    def __insert_user(self, user, values):
        """
        """
        self.module.log(msg=f"__insert_user('{user}')")

        given_name = values.get("given_name", None)
        sn = values.get("sn", '')
        mail = values.get("mail", '')
        uid = values.get("uid", None)
        primary_group = values.get("primary_group", None)
        other_groups = values.get("other_groups", [])
        passwords = values.get("pass", None)
        if passwords:
            pass_sha256 = passwords.get("sha256", None)
            pass_bcrypt = passwords.get("bcrypt", None)
        ssh_keys = values.get("ssh_keys", [])
        otp_secret = values.get("otp_secret", None)
        yubikey = values.get("yubikey", None)
        login_shell = values.get("login_shell", '')
        home_dir = values.get("home_dir", '')
        capabilities = values.get("capabilities", {})

        self.module.log(msg=f"  - passwords  : '{passwords}'")
        self.module.log(msg=f"  - pass sha256: '{pass_sha256}'")

        query = f"""
          insert into users
          (`name`, `uidnumber`, `primarygroup`, `givenname`,`sn`, `mail`, `loginshell`, `homedirectory`)
           values
          ('{user}', '{uid}', '{primary_group}', '{given_name}', '{sn}', '{mail}', '{login_shell}', '{home_dir}')
        """

        self.module.log(msg=f"  - query: {query}'")

        result, last_inserted_id, msg = self.__execute_query(query)

        if result and last_inserted_id:
            self.module.log(msg=f"  - last_inserted_id: {last_inserted_id}'")

            if pass_sha256:
                """
                """
                query = f"update users set passsha256 = '{pass_sha256}' where uidnumber = '{uid}' and id = {last_inserted_id}"
                self.module.log(msg=f"  - query: {query}'")

                result, last_inserted_id, msg = self.__execute_query(query)

            if pass_bcrypt:
                """
                """
                query = f"update users set passbcrypt = '{pass_bcrypt}' where uidnumber = '{uid}' and id = {last_inserted_id}"
                self.module.log(msg=f"  - query: {query}'")

                result, last_inserted_id, msg = self.__execute_query(query)

            if otp_secret:
                """
                """
                query = f"update users set otpsecret = '{otp_secret}' where uidnumber = '{uid}' and id = {last_inserted_id}"
                self.module.log(msg=f"  - query: {query}'")

                result, last_inserted_id, msg = self.__execute_query(query)

            if len(ssh_keys) > 0:
                """
                """
                _ssh_keys = " ".join(ssh_keys)

                query = f"update users set sshkeys = '{_ssh_keys}' where uidnumber = '{uid}' and id = {last_inserted_id}"
                self.module.log(msg=f"  - query: {query}'")

                result, last_inserted_id, msg = self.__execute_query(query)

    def __update_user(self, user, values):
        """
        """
        self.module.log(msg=f"__update_user('{user}')")

        given_name = values.get("given_name", None)
        sn = values.get("sn", '')
        mail = values.get("mail", '')
        uid = values.get("uid", None)
        primary_group = values.get("primary_group", None)
        other_groups = values.get("other_groups", [])
        passwords = values.get("pass", None)
        if passwords:
            pass_sha256 = passwords.get("sha256", None)
            pass_bcrypt = passwords.get("bcrypt", None)
        ssh_keys = values.get("ssh_keys", [])
        otp_secret = values.get("otp_secret", None)
        yubikey = values.get("yubikey", None)
        login_shell = values.get("login_shell", '')
        home_dir = values.get("home_dir", '')
        capabilities = values.get("capabilities", {})

        self.module.log(msg=f"  - passwords  : '{passwords}'")

        pass

    def __execute_query(self, query):
        """
        """
        import sqlite3

        try:
            conn = sqlite3.connect(
                self.database_file,
                isolation_level=None,
                detect_types=sqlite3.PARSE_COLNAMES
            )

            cursor = conn.execute(query)

            last_inserted_id = cursor.lastrowid

            return True, last_inserted_id, ""

        except sqlite3.Error as er:
            self.module.log(msg=f"SQLite error: '{(' '.join(er.args))}'")
            self.module.log(msg=f"Exception class is '{er.__class__}'")

            _msg = (' '.join(er.args))

            return False, -1, _msg

    def __create_directory(self, dir):
        """
        """
        try:
            os.makedirs(dir, exist_ok=True)
        except FileExistsError:
            pass

        if os.path.isdir(dir):
            return True
        else:
            return False


    def __checksum_file(self, checksum, checksum_file):
        """
        """
        with open(checksum_file, "w") as f:
            f.write(checksum)

        return True

    def __read_checksum_file(self, checksum_file):
        """
        """
        if os.path.exists(checksum_file):
            with open(checksum_file, "r") as f:
                return f.readlines()[0]

        return None

# ===========================================
# Module execution.
#


def main():
    """
    """
    module = AnsibleModule(
        argument_spec=dict(
            database_type=dict(
                default="sqlite",
                choices=["sqlite", "mysql", "mariadb"]
            ),
            groups=dict(
                type=dict,
                requiered=False
            ),
            users=dict(
                type=dict,
                requiered=False
            )
        ),
        supports_check_mode=False,
    )

    o = GlAuthBackendData(module)
    result = o.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
