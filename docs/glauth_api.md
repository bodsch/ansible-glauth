 
## `glauth_api`

| parameter        | glauth version | type      | default     | description |
| :---             | :---           | :---      | :---        | :---        |
| `enabled`        | 2.1            | `bool`    | `false`     |             |
| `internals`      | 2.1            | `bool`    | `true`      |             |
| `listen.address` | 2.1            | `string`  | `127.0.0.1` |             |
| `listen.port`    | 2.1            | `int`     | `5555`      |             |
| `tls.cert_file`  | 2.1            | `string`  | `-`         |             |
| `tls.key_file`   | 2.1            | `string`  | `-`         |             |
| `secret_token`   | 2.1            | `string`  | `-`         |             |

```yaml
glauth_api:
  enabled: true
  listen:
    address: "0.0.0.0"
```
