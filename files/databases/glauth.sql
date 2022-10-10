---
--- taken from https://github.com/glauth/glauth/blob/master/v2/pkg/plugins/mysql.go
---
---

CREATE TABLE IF NOT EXISTS users (
	id INTEGER AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(64) NOT NULL,
	uidnumber INTEGER NOT NULL,
	primarygroup INTEGER NOT NULL,
	othergroups VARCHAR(1024) DEFAULT '',
	givenname VARCHAR(64) DEFAULT '',
	sn VARCHAR(64) DEFAULT '',
	mail VARCHAR(254) DEFAULT '',
	loginshell VARCHAR(64) DEFAULT '',
	homedirectory VARCHAR(64) DEFAULT '',
	disabled SMALLINT  DEFAULT 0,
	passsha256 VARCHAR(64) DEFAULT '',
	passbcrypt VARCHAR(64) DEFAULT '',
	otpsecret VARCHAR(64) DEFAULT '',
	yubikey VARCHAR(128) DEFAULT '',
	custattr TEXT DEFAULT '{}')
