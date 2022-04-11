# fail2ban-from-s3

Grabs a JSON-encoded list of things to ban and bans them using [fail2ban](https://www.fail2ban.org).

# Installation

`python -m pip install --upgrade fail2ban-importer`

# Usage

`fail2ban-importer [--oneshot|--dryrun]`

# Configuration

The following paths will be tested (in order) and the first one loaded:

 - `./fail2ban-importer.json`
 - `/etc/fail2ban-importer.json`
 - `~/.config/fail2ban-importer.json`

## Fields 

Note the `fail2ban_jail` field. If you're going to pick up your logs from fail2ban, and use them for the source of automation, make sure to filter out the actions by this system - otherwise you'll end up in a loop!

| Field Name        | Value Type | Default Value     | Required | Description |
| ---               |     ---    |     ---           |  ---     |    ---   |
| `download_module` | `str`      | `http`            | No       | The download module to use (either `http` or `s3`)  |
| `fail2ban_jail`   | `str`      | unset             | **Yes**  | The jail to use for banning - DO NOT REUSE AN EXISTING JAIL |
| `source`          | `str`      | `blank`           | **Yes**  | Where to pull the file from, can be a `http(s)://` or `s3://` URL. |
| `fail2ban_client` | `str`      | `fail2ban_client` | No       |  The path to the `fail2ban-client` executable, in case it's not in the user's `$PATH` |
| `schedule_mins`   | `int`      | 15                | No       | How often to run the action. |
| `s3_endpoint`     | `str`      |                   | No       | The endpoint URL if you need to force it for s3, eg if you're using minio or another S3-compatible store. |
| `s3_v4`           | `bool`     | `false`           | No       | Whether to force `s3_v4` requests (useful for minio) |
| `s3_minio`        | `bool`     | `false`           | No       | Enable minio mode, force `s3_v4` requests |

## HTTP(S) Source

```json fail2ban-importer.json
x
{
    "source": "https://example.com/fail2ban.json",
    "fail2ban_client": "/usr/bin/fail2ban-client",
    "fail2ban_jail" : "automated",
    "schedule_mins" : 15
}
```

## S3-compatible Source

You can use the usual [boto3 AWS configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration), or put the options in the config file.

```json fail2ban-importer.json
{
    "source": "s3://my-magic-fail2ban-bucket/fail2ban.json",
    "AWS_ACCESS_KEY_ID" : "exampleuser",
    "AWS_SECRET_ACCESS_KEY" : "hunter2",
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
    "jail": "sshd",
    "ip": "196.30.15.254"
  },
  {
    "jail": "sshd",
    "ip": "119.13.89.28"
  }
]
```

# Thanks

 - [fail2ban](https://www.fail2ban.org)
 - [boto3](https://boto3.amazonaws.com)
 - [requests](https://docs.python-requests.org/en/master/index.html)
 - [schedule](https://schedule.readthedocs.io/en/stable/)