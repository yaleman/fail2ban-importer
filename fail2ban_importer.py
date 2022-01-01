#!/usr/bin/env python3

""" loads things from s3 or an s3-like thing, or maybe just https """

# TODO: whitelisting

import json
from json.decoder import JSONDecodeError
import logging
import os
import sys
import subprocess
from typing import Optional, TypedDict, Callable  # Type, Union,

VALID_LOGLEVELS = ["CRITICAL", "DEBUG", "ERROR", "FATAL", "INFO", "WARNING"]
loglevel = os.getenv("LOG_LEVEL", "DEBUG").upper()
if not hasattr(logging, loglevel):
    raise ValueError(
        f"Invalid log level specified, got {loglevel}, should be in {VALID_LOGLEVELS}"
    )

logging.basicConfig(
    format="%(levelname)s %(message)s", level=getattr(logging, loglevel)
)

logging.debug("Running %s", os.path.basename(__file__))

FAILED_IMPORT = False
try:
    import boto3
    import requests
except ImportError as error_message:
    FAILED_IMPORT = True
    logging.error("Failed to import package: %s", error_message)

if FAILED_IMPORT:
    sys.exit(1)

CONFIG_FILE = "fail2ban_importer.json"

CONFIG_FILES = [
    CONFIG_FILE,
    f"~/.config/{CONFIG_FILE}",
    f"/etc/{CONFIG_FILE}",
]

EXPECTED_CONFIG_FIELDS = [
    "source",
    "fail2ban_client",
    "jail_field",
    "jail_target",
]

REQUIRED_CONFIG_FIELDS = [
    "source",
]

CONFIG_TYPING = TypedDict(
    "CONFIG_TYPING",
    {
        "source": str,
        "download_method": Callable,
        "fail2ban_client": str,
        "jail_field": str,
        "jail_target": str,
    },
)


class UnsupportedSourceType(Exception):
    """Unsupported Source"""


def load_config() -> Optional[CONFIG_TYPING]:
    """looks for config files and loads them"""
    for filename in CONFIG_FILES:
        if os.path.exists(filename):
            logging.debug("Using config file: %s", filename)
            with open(filename, "r", encoding="utf8") as file_handle:
                try:
                    imported_config: CONFIG_TYPING = json.load(file_handle)

                    return imported_config
                except JSONDecodeError as json_error:
                    logging.error(
                        "Failed to load %s due to JSON error: %s", filename, json_error
                    )
    return None


def download_with_requests(download_config: CONFIG_TYPING) -> Optional[dict]:
    """ downloads the source file using the requests library """
    logging.debug("Download config: %s", download_config)
    request_method = str(download_config.get("request_method", "GET"))
    response = requests.request(
        url=download_config["source"],
        method=request_method,
    )
    response.raise_for_status()

    try:
        response_data = response.json()
    except JSONDecodeError as json_error:
        logging.error("Failed to parse response: %s", json_error)
        logging.error("First 1000 chars of response: %s", response.content[:1000])
        sys.exit(1)

    return response_data


def download_with_s3(download_config: dict) -> Optional[dict]:
    """ downloads the source file using the requests library """
    logging.debug(download_config)
    _s3client = boto3.client("s3")
    # s3client.get_object(Bucket=download_config["bucket"], Key="filename")

    return {}


def parse_config(config_to_parse: CONFIG_TYPING) -> CONFIG_TYPING:
    """ loads the data file """
    failed_to_load = False
    for field in config_to_parse:
        if field not in EXPECTED_CONFIG_FIELDS:
            logging.warning("Found extra field in config: '%s' ignoring.", field)
    for field in REQUIRED_CONFIG_FIELDS:
        if field not in config_to_parse:
            failed_to_load = True
            logging.error("Failed to find %s in config, bailing.", field)
    if failed_to_load:
        sys.exit(1)
    if config_to_parse["source"].startswith("http"):
        config_to_parse["download_method"] = download_with_requests
    elif config_to_parse["source"].startswith("s3:"):
        config_to_parse["download_method"] = download_with_s3
    else:
        config_to_parse["download_method"] = sys.exit
        raise UnsupportedSourceType(
            f"Can't handle this: {config_to_parse.get('source')!r}"
        )

    if "jail_field" not in config_to_parse:
        config_to_parse["jail_field"] = "jail"
    if "jail_target" not in config_to_parse:
        config_to_parse["jail_target"] = "target"

    if "fail2ban_client" not in config_to_parse:
        logging.debug("Setting default fail2ban-client to 'fail2ban-client")
        config_to_parse["fail2ban_client"] = "fail2ban-client"

    return config_to_parse


config: Optional[CONFIG_TYPING] = load_config()
if not config:
    logging.error("Failed to find/load config file.", file=sys.stderr)
    sys.exit(1)

logging.debug("Config: %s", json.dumps(config, indent=4, ensure_ascii=False))

config = parse_config(config)

logging.debug(json.dumps(config, indent=4, ensure_ascii=False, default=str))

if "download_method" in config:
    data: dict = config["download_method"](config)

for item in data:
    logging.info(
        "jail=%s target=%s",
        item[config["jail_field"]],
        item[config["jail_target"]],
    )
    if '--dryrun' not in sys.argv:
        subprocess.call(
            [
                config["fail2ban_client"],
                "set",
                item[config["jail_field"]],
                "banip",
                item[config["jail_target"]],
            ],
        )
