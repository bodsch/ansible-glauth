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

              ## -> result_state = self.import_users()


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

        self.module.log(msg=f" - changed '{changed}'")
        self.module.log(msg=f" - failed  '{failed}'")

        result_msg = {k: v.get('state') for k, v in combined_d.items()}

        return dict(
            rc=0,
            failed=failed,
            changed=changed,
            msg=result_msg
        )


    def import_groups(self):
        """
            CREATE TABLE IF NOT EXISTS groups (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL,
              gidnumber INTEGER NOT NULL
            );
        """
        for group, values in self.groups.items():
            """
                name        LDAP group name (i.e. cn or ou depending on context)
                gidnumber   LDAP GID attribute
            """
            self.module.log(msg=f"  - group: {group}")

            gid = values.get('gid')
            include_groups = values.get("include_groups", [])

            group_exists, error, existing_groupid, error_message = self.__check_database_value('groups', 'name', group)

            if group_exists:
                """
                  update
                """
                query = f"update groups set gidnumber = {gid} where name = '{group}'"
                success, _, msg = self.__execute_query(query)

            else:
                """
                  insert
                """
                # success, msg = self.__insert_user(user, values)
                query = f"insert or replace into groups (`name`, `gidnumber`) values ('{group}', '{gid}')"
                success, last_inserted_id, msg = self.__execute_query(query)

                existing_groupid = last_inserted_id

            if success:
                """
                """
                query = f"delete from includegroups where parentgroupid = {existing_groupid}"
                success, _, msg = self.__execute_query(query)

                if len(include_groups) > 0 and existing_groupid:
                    for include_group in include_groups:
                        """
                          'includegroupid' is the reference to id in 'users'!

                          parentgroupid   the LDAP group id containing another group, used by glauth
                          ncludegroupid   the LDAP group id contained in the parent group, used by glauth
                        """
                        _id = self.__group_id(int(include_group))

                        if _id:
                            query = f"insert into includegroups (`parentgroupid`, `includegroupid`) values('{existing_groupid}', '{_id}')"
                            result, last_inserted_id, msg = self.__execute_query(query)


    def import_users(self):
        """
          CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            uidnumber INTEGER NOT NULL,
            primarygroup INTEGER NOT NULL,
            othergroups TEXT DEFAULT '',
            givenname TEXT DEFAULT '',
            sn TEXT DEFAULT '',
            mail TEXT DEFAULT '',
            loginshell TYEXT DEFAULT '',
            homedirectory TEXT DEFAULT '',
            disabled SMALLINT  DEFAULT 0,
            passsha256 TEXT DEFAULT '',
            passbcrypt TEXT DEFAULT '',
            otpsecret TEXT DEFAULT '',
            sshkeys TEXT DEFAULT '',
            yubikey TEXT DEFAULT '',
            custattr TEXT DEFAULT '{}'
          );

        """
        # self.module.log(msg=f"users: {self.users}'")
        result_state = []

        for user, values in self.users.items():
            """
            """
            _failed = False

            self.module.log(msg=f"  - user: {user}'")

            res = {}

            _checksum_file = os.path.join(self.checksum_directory, f"{user}.checksum")

            old_checksum = self.__read_checksum_file(_checksum_file)
            cur_checksum = self.__checksum(json.dumps(values, sort_keys=True))

            self.module.log(msg=f"    old_checksum : '{old_checksum}'")
            self.module.log(msg=f"    cur_checksum : '{cur_checksum}'")

            if old_checksum and old_checksum == cur_checksum:

                res[user] = dict(
                    changed=False,
                    state="User has not changed."
                )
            else:
                # first step:
                # take a lock into the database
                # user_exists, error, existing_userid, error_message = self.__list_user(user)
                user_exists, error, existing_userid, error_message = self.__check_database_value('users', 'name', user)

                if user_exists:
                    """
                      update
                    """
                    success, msg = self.__update_user(user, values)

                    if success:
                        _failed = False

                    res[user] = dict(
                        changed = True,
                        failed = success,
                        state="User successfully updated."
                    )

                else:
                    """
                      insert
                    """
                    success, msg = self.__insert_user(user, values)

                    if success:
                        _failed = False

                    res[user] = dict(
                        changed = True,
                        failed = _failed,
                        state="User successfully created."
                    )

                self.module.log(msg=f"    success: {success} '{msg}'")

                if success:
                    self.__checksum_file(cur_checksum, _checksum_file)

            result_state.append(res)

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


    def __check_database_value(self, table, where, value):
        """
        """
        import sqlite3

        try:
          conn = sqlite3.connect(
              self.database_file,
              isolation_level=None,
              detect_types=sqlite3.PARSE_COLNAMES
          )
          conn.row_factory = lambda cursor, row: row[0]

          query = f"select id from {table} where {where} = '{value}'"

          cursor = conn.execute(query)

          userid = cursor.fetchall()

          if isinstance(userid, list) and len(userid) > 0:
              existing_userid = userid[0]
          else:
              existing_userid = 0

          if existing_userid == 0:
              _exists = False
              _error = False
              _msg = f"The {where} does not exist."
          else:
              _exists = True
              _error = False
              _msg = f"{where} already created."

        except sqlite3.Error as er:
            self.module.log(msg=f"SQLite error: '{(' '.join(er.args))}'")
            self.module.log(msg=f"Exception class is '{er.__class__}'")

            _exists = False
            _error = True
            _msg = (' '.join(er.args))

        return _exists, _error, existing_userid, _msg


    def __insert_user(self, user, values):
        """
          # https://glauth.github.io/docs/databases.html

          Note that, in `users`, `othergroups` is a comma-separated list of group ids.
        """
        self.module.log(msg=f"__insert_user('{user}')")

        given_name = values.get("given_name", None)             # LDAP name (i.e. cn, uid)
        sn = values.get("sn", '')                               # LDAP sn attribute, i.e. an account’s last name
        mail = values.get("mail", '')                           # LDAP mail attribute, i.e. email address; also used as userPrincipalName
        uid = values.get("uid", None)                           # LDAP UID attribute
        primary_group = values.get("primary_group", None)       # An LDAP group’s GID attribute; also used to build ou attribute; used to build memberOf
        other_groups = values.get("other_groups", [])           # A comma-separated list of GID attributes; used to build memberOf
        passwords = values.get("pass", None)                    #
        if passwords:                                           #
            pass_sha256 = passwords.get("sha256", None)         # SHA256 account password
            pass_bcrypt = passwords.get("bcrypt", None)         # BCRYPT-encrypted account password
        ssh_keys = values.get("ssh_keys", [])                   # A comma-separated list of sshPublicKey attributes
        otp_secret = values.get("otp_secret", None)             # OTP secret, for two-factor authentication
        yubikey = values.get("yubikey", None)                   # UBIKey, for two-factor authentication
        login_shell = values.get("login_shell", '')             # LDAP loginShell attribute, pushed to the client, may be ignored
        home_dir = values.get("home_dir", '')                   # LDAP homeDirectory attribute, pushed to the client, may be ignored
        capabilities = values.get("capabilities", {})           # used to retrieve capabilities granted to users linked to it from the users table
        custom_attrs = values.get("custom_attrs", {})           # A JSON-encoded string, containing arbitrary additional attributes; must be {} by default

        # gid = self.__group_id(int(primary_group))

        query = f"""
          insert into users
          (`name`, `uidnumber`, `primarygroup`, `givenname`,`sn`, `mail`, `loginshell`, `homedirectory`)
           values
          ('{user}', '{uid}', '{primary_group}', '{given_name}', '{sn}', '{mail}', '{login_shell}', '{home_dir}')
        """
        # self.module.log(msg=f"  - query: {query}")

        result, last_inserted_id, msg = self.__execute_query(query)

        self.module.log(msg=f"  - result: {result}, last_inserted_id: {last_inserted_id}, msg: {msg}")

        if result and last_inserted_id:
            """
            """
            if other_groups:
                _other_groups=",".join(other_groups)
                self.__update_user_single_field(uid, "other_groups", _other_groups)

            if pass_sha256:
                self.__update_user_single_field(uid, "passsha256", pass_sha256)

            if pass_bcrypt:
                self.__update_user_single_field(uid, "passbcrypt", pass_bcrypt)

            if otp_secret:
                self.__update_user_single_field(uid, "otpsecret", otp_secret)

            if len(ssh_keys) > 0:
                _ssh_keys = ",".join(ssh_keys)
                self.__update_user_single_field(uid, "sshkeys", _ssh_keys)

            if len(capabilities) > 0:
                """
                    CREATE TABLE IF NOT EXISTS capabilities (
                      id INTEGER PRIMARY KEY,
                      userid INTEGER NOT NULL,
                      action TEXT NOT NULL,
                      object TEXT NOT NULL
                    );
                """
                for action, obj in capabilities.items():
                    """
                        userid  internal user id number, used by glauth
                        action  string representing an allowed action, e.g. “search”
                        object  string representing scope of allowed action, e.g. “ou=superheros,dc=glauth,dc=com”
                    """
                    _object = obj.get('object')
                    query = f"insert or replace into capabilities (`userid`, `action`, `object`) values ({last_inserted_id}, '{action}', '{_object}')"

                    result, last_inserted_id, msg = self.__execute_query(query)

                    self.module.log(msg=f"  - result: {result}, last_inserted_id: {last_inserted_id}, msg: {msg}")

                    if not result:
                        self.module.log(msg=f"  ERROR : {msg}")
                        break

        return result, ""


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

        # self.module.log(msg=f"  - passwords  : '{passwords}'")

        query = f"update users set `uidnumber` = '{uid}', `primarygroup` = '{primary_group}', `givenname` = '{given_name}' ,`sn` = '{sn}', `mail` = '{mail}', `loginshell` = '{login_shell}', `homedirectory` = '{home_dir}' where name = '{user}'"
        self.module.log(msg=f"  - query: {query}")

        result, _, msg = self.__execute_query(query)

        self.module.log(msg=f"  - {result} / {msg}")

        if result:
            if pass_sha256:
                self.__update_user_single_field(uid, "passsha256", pass_sha256)

            if pass_bcrypt:
                self.__update_user_single_field(uid, "passbcrypt", pass_bcrypt)

            if otp_secret:
                self.__update_user_single_field(uid, "otpsecret", otp_secret)

            if len(ssh_keys) > 0:
                _ssh_keys = " ".join(ssh_keys)
                self.__update_user_single_field(uid, "sshkeys", _ssh_keys)

        return result, msg


    def __update_user_single_field(self, uid, field, value):
        """
        """
        query = f"update users set {field} = '{value}' where uidnumber = '{uid}'"

        result, last_inserted_id, msg = self.__execute_query(query)


    def __execute_query(self, query):
        """
          return:
            if successfully    : True, last_inserted_id, message
            if NOT successfully: False, -1, error_message
        """
        # self.module.log(msg=f"__execute_query({query})")

        import sqlite3

        try:
            conn = sqlite3.connect(
                self.database_file,
                isolation_level=None,
                detect_types=sqlite3.PARSE_COLNAMES
            )

            if "select" in query:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query)

                rows = cursor.fetchall()
                # result as json
                r = json.dumps( [dict(ix) for ix in rows] )

                return True, r, ""

            else:
                cursor = conn.execute(query)
                last_inserted_id = cursor.lastrowid

                return True, last_inserted_id, "query successfully executed"

        except sqlite3.Error as er:
            self.module.log(msg=f"SQLite error: '{(' '.join(er.args))}'")
            self.module.log(msg=f"Exception class is '{er.__class__}'")

            _msg = (' '.join(er.args))

            return False, -1, _msg


    def __group_id(self, gid):
        """
        """
        _id = None

        state, data = self.__group_data()

        if isinstance(data, str):
            data = json.loads(data)

        if state:
            data = [d for d in data if int(d.get('gidnumber')) == int(gid)]

            if len(data) > 0:
                _id = data[0].get("id", None)

        return _id


    def __group_data(self):
        """
          return a dictionary with all group informations
        """
        query = "select id, name, gidnumber from groups order by gidnumber"

        result, data, _ = self.__execute_query(query)

        return result, data


    def __user_data(self):
        """
          return a dictionary with a subset of user informations
        """
        query = "select id, name, uidnumber from users order by uidnumber"

        result, data, _ = self.__execute_query(query)

        return result, data


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
        self.module.log(msg=f"    write checksum_file : '{checksum_file}'")

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
