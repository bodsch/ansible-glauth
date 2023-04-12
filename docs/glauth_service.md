 
## `glauth_service`

| parameter        | glauth version | type      | default | description                            |
| :---             | :---           | :---      | :---    | :---                                   |
| `aws.key_id`     | 2.1            | `string`  | `-`     | AWS Key ID                             |
| `aws.secret_key` | 2.1            | `string`  | `-`     | AWS Secret Key                         |
| `aws.region`     | 2.1            | `string`  | `-`     | AWS Region                             |
| `listen.ldap`    | 2.1            | `string`  | `-`     | Listen address for the LDAP server     |
| `listen.ldaps`   | 2.1            | `string`  | `-`     | Listen address for the LDAPS server    |
| `tls.cert_file`  | 2.1            | `string`  | `-`     | Path to cert file for the LDAPS server |
| `tls.key_file`   | 2.1            | `string`  | `-`     | Path to key file for the LDAPS server  |


```yaml
glauth_service:
  aws:
    key_id: ""
    secret_key: ""
    region: ""
  listen:
    ldap: ""
    ldaps: ""
  tls:
    cert_file: "/etc/glauth/certs/molecule.lan.pem"
    key_file: "/etc/glauth/certs/molecule.lan.key"
```
