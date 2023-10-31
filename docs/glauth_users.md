 
## `glauth_users`

| parameter          | glauth version | type     | default | description |
| :---               | :---           | :---     | :---    | :---        |
| `enabled`          | 2.1            | `bool`   | `-`     |             |
| `given_name`       | 2.1            | `string` | `-`     | First Name  |
| `sn`               | 2.1            | `string` | `-`     | Last Name   |
| `mail`             | 2.1            | `string` | `-`     |             |
| `uid`              | 2.1            | `int`    | `-`     | User ID     |
| `primary_group`    | 2.1            | `int`    | `-`     |             |
| `other_groups`     | 2.1            | `list`   | `-`     |             |
| `pass.sha256`      | 2.1            | `string` | `-`     |             |
| `pass.sha256_apps` | 2.1            | `list`   | `-`     | Specify an array of app passwords which can also succesfully bind - these bypass the OTP check. Hash the same way as password.            |
| `pass.bcrypt`      | 2.1            | `string` | `-`     |             |
| `pass.bcrypt_apps` | 2.1            | `list`   | `-`     | Specify an array of app passwords which can also succesfully bind - these bypass the OTP check. Hash the same way as password.            |
| `ssh_keys`         | 2.1            | `list`   | `-`     |             |
| `otp_secret`       | 2.1            | `string` | `-`     |             |
| `yubikey`          | 2.1            | `string` | `-`     |             |
| `login_shell`      | 2.1            | `string` | `-`     |             |
| `home_dir`         | 2.1            | `string` | `-`     |             |
| `capabilities`     | 2.1            | `dict`   | `-`     |             |
| `custom_attrs`     | 2.1            | `dict`   | `-`     |             |

### Passwords

> Read also the original [security](https://glauth.github.io/docs/security.html) documentation!

#### create bcrypt password

In the configuration file, the password is "coded" in hexadecimal numbers, i.e. each character is replaced by two characters from 0-9 and A-F.

You need [xxd](https://command-not-found.com/xxd) for the following steps:

If you want to insert a bcrypt string into the config, you have to convert your brcrypt password to hexadecimal representation.

```shell
python -c 'import bcrypt; print(bcrypt.hashpw(b"xxx", bcrypt.gensalt(rounds=15)).decode("ascii"))' | xxd   -p -c 150
243262243135246974444d364b7534642e6c2e78614c49452e6351692e48663372642e753863796e704c4a4b6b623176674f6c72763453525976362e0a
```
The result can then be used in the configuration.

You can check the string in the following way
```shell
echo 243262243135246f74394a6c5377303338346a47364454654c4758652e7367347a4b3049724b5a4a64466832575775647355686c367964496338624f0a | xxd -r -p
$2b$15$ot9JlSw0384jG6DTeLGXe.sg4zK0IrKZJdFh2WWudsUhl6ydIc8bO
```

A password has the following structure:
`$2y$2^<number of rounds>$<salt>$<hash>`

e.g: `$2a$12$vXQCX9zGGAj22vNazNrBz.pBCWsUuLH.QBLImlra61i70D/MFDhKa`

For the 2a vs. 2y prefix, see [stackoverflow](https://stackoverflow.com/a/36225192).


#### create sha256 password

#### with openssl

```bash
echo -n "PASSWORD" | openssl dgst -sha256
(stdin)= 0be64ae89ddd24e225434de95d501711339baeee18f009ba9b4369af27d30d60
```

#### with python

```bash
python -c 'import hashlib; print(hashlib.sha256(b"xxx").hexdigest())'
cd2eb0837c9b4c962c22d2ff8b5441b7b45805887f051d39bf133b583baf6860
```

### `capabilities`

[see upstream doku](https://glauth.github.io/docs/capabilities.html)

| parameter | glauth version | type    | default | description |
| :---      | :---           | :---    | :---    | :---        |
| `object`  | 2.1            | ``      | `-`     |             |

#### `custom_attrs`

[see upstream doku](https://glauth.github.io/docs/custom-attributes.html)

| parameter | glauth version | type    | default | description |
| :---      | :---           | :---    | :---    | :---        |
| ``        | 2.1            | ``      | `-`     |             |
| ``        | 2.1            | ``      | `-`     |             |

```yaml
glauth_users:
  admin:
    enabled: true
    given_name: Admin
    mail: "admin@matrix.lan"
    uid: 3000
    primary_group: 3000
    pass:
      sha256: "6b7556f632dc73ea7470a0116d6e55880fda6ca50575b72c7cc5f13df53a2623"
    login_shell: "/bin/bash"
    capabilities:
      "*":
        object: "dc=molecule,dc=lan"

  bodsch:
    given_name: "B."
    sn: "Schulz"
    uid: 6000
    primary_group: 6000
    other_groups:
      - 4001
    pass:
      sha256: "6b7556f632dc73ea7470a0116d6e55880fda6ca50575b72c7cc5f13df53a2623"
      sha256_apps:
        - "fc6be9b218afa2ce37409580b8a4907feb6c1ea878d1222e4d2b84e81c1c0e47"
        - "cd2eb0837c9b4c962c22d2ff8b5441b7b45805887f051d39bf133b583baf6860"
    ssh_keys:
      - "ssh-ed25519 ... bodsch@matrix.lan"
    login_shell: "/bin/bash"
    home_dir: "/home/bodsch"
    capabilities:
      "search":
        object: "dc=molecule,dc=lan"
```

