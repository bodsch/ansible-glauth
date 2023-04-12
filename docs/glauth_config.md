
## `glauth_config`

| parameter          | glauth version | type     | default | description |
| :---               | :---           | :---     | :---    | :---        |
| `debug`            | 2.1            | `bool`   | `false` | Enable Debug |
| `syslog`           | 2.1            | `bool`   | `true`  |             |
| `watch_config`     | 2.1            | `bool`   | `true`  | Enable hot-reload of configuration on changes<br>**does NOT work [ldap], [ldaps], [backend] or [api] sections** |
| `yubikey.clientid` | 2.1            | `string` | `-`     |             |
| `yubikey.secret`   | 2.1            | `string` | `-`     |             |

```yaml
glauth_config:
  ldaps:
    enabled: false
    listen:
      address: "0.0.0.0"
      port: "636"
    tls:
      cert_file: "/etc/glauth/certs/molecule.lan.pem"
      key_file: "/etc/glauth/certs/molecule.lan.key"

``` 
