# fail2ban-from-s3

Grabs a JSON-encoded list of things to ban and bans them using [fail2ban](https://www.fail2ban.org).

# Installation

`python3 -m pip install --upgrade fail2ban-importer`

# Usage

`fail2ban_importer [--oneshot|--dryrun]`

# Configuration

Config file can be in one of the following paths:

 - `./fail2ban_importer.json`
 - `~/.config/fail2ban_importer.json`
 - `/etc/fail2ban_importer.json`

Fields 
| Field Name | Value Type | Default Value | Description | Required |
| --- | --- | --- | --- | --- |
| `source` | `str` | | Where to pull the file from, can be a `http(s)://` or `s3://` URL. | **Yes** |
| `fail2ban_client` | `str` | `fail2ban_client` | The path to the `fail2ban-client` executable, in case it's not in the user's `$PATH` | No |
| `jail_field` | `str` | `jail` | The field to pull the target fail2ban [jail] from in your file. | No |
| `jail_target` | `str` | `target` | The field to pull the target IP from in your file. | No |
| `schedule_mins` | `int` | 5 | How often to run the action. | No |
| `s3_endpoint` | `str` | | The endpoint URL if you need to force it for s3, eg if you're using minio or another S3-compatible store. | No |
| `s3_v4` | `bool` | `false`  | Whether to force `s3_v4` requests (useful for minio) | No |
| `s3_minio` | `bool` | `false` | Enable minio mode, force `s3_v4` requests | No |

## HTTPS Source

```json fail2ban_importer.json
{
    "source": "https://example.com/fail2ban.json",
    "jail_field": "service",
    "jail_target": "src",
    "fail2ban_client": "/usr/bin/fail2ban-client",
    "schedule_mins" : 1
}
```

## S3-compatible Source

You can use the usual [boto3 AWS configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration), or put the options in the config file.

```json fail2ban_importer.json
{
    "source": "s3://my-magic-fail2ban-bucket/fail2ban.json",
    "AWS_ACCESS_KEY_ID" : "exampleuser",
    "AWS_SECRET_ACCESS_KEY" : "hunter2",
    "jail_field": "service",
    "jail_target": "src",
    "schedule_mins" : 1
}
```

If you're using minio as your backend, you should add the following additional options to the config file:

```json
{
    "s3_v4" : true,
    "s3_endpoint" : "https://example.com",
}
```

# Example source data file

```json data.json
[
  {
    "ban_time": "1640997884.011",
    "host": "host1.example.com",
    "service": "sshd",
    "src": "196.30.15.254"
  },
  {
    "ban_time": "1640996178.501",
    "host": "host2.example.com",
    "service": "https",
    "src": "119.13.89.28"
  }
]
```

# Thanks

 - [fail2ban](https://www.fail2ban.org)
 - [boto3](https://boto3.amazonaws.com)
 - [requests](https://docs.python-requests.org/en/master/index.html)
 - [schedule](https://schedule.readthedocs.io/en/stable/)