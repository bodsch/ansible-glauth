---
--- taken https://github.com/glauth/glauth/blob/master/v2/pkg/plugins/sqlite.go
---
---
BEGIN TRANSACTION;

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

CREATE TABLE IF NOT EXISTS groups (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  gidnumber INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS includegroups (
  id INTEGER PRIMARY KEY,
  parentgroupid INTEGER NOT NULL,
  includegroupid INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS capabilities (
  id INTEGER PRIMARY KEY,
  userid INTEGER NOT NULL,
  action TEXT NOT NULL,
  object TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_name on users(name, uidnumber);
CREATE UNIQUE INDEX IF NOT EXISTS idx_group_name on groups(name, gidnumber);

COMMIT;
