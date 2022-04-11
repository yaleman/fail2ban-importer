#!/usr/bin/env python3

""" loads things from s3 or an s3-like thing, or maybe just https """

# TODO: allow-listing

import json
from json.decoder import JSONDecodeError

import subprocess
import logging
import os
import sys
from time import sleep
from typing import Callable, TypedDict, Optional

from .fail2ban_types import ConfigFile

VALID_LOGLEVELS = ["CRITICAL", "DEBUG", "ERROR", "FATAL", "INFO", "WARNING"]

loglevel = os.getenv("LOG_LEVEL", "INFO").upper()
if not hasattr(logging, loglevel):
    raise ValueError(
        f"Invalid log level specified, got {loglevel}, should be in {VALID_LOGLEVELS}"
    )

logging.basicConfig(
    format="%(levelname)s %(message)s", level=getattr(logging, loglevel)
)

logging.debug("Running %s", os.path.basename(__file__))

main_failed_import = False  # pylint: disable=invalid-name
try:
    # import boto3
    # import boto3.session
    # import botocore.exceptions
    import requests
    import schedule  # type: ignore
except ImportError as error_message:
    main_failed_import = True  # pylint: disable=invalid-name
    logging.error("Failed to import package: %s", error_message)
if main_failed_import:
    sys.exit(1)


def ban_action(client_command: str, jail_name: str, target_ip: str) -> bool:
    """ actually does the ban bit """
    command = [
        client_command,
        "set",
        jail_name,
        "banip",
        target_ip,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True)
        # logging.debug(result)
        if result.stdout.decode("utf-8").strip() == "1":
            logging.debug("Success")
        elif result.stdout.decode("utf-8").strip() == "0":
            logging.debug("%s already in %s", target_ip, jail_name)
        else:
            logging.error("Unexpected output: %s", result.stdout.decode("utf-8").strip())
    except subprocess.CalledProcessError as called_process_error:
        command_joined = " ".join(command)
        logging.error(
            "Error running '%s': stdout='%s', stderr='%s'",
            command_joined,
            called_process_error.stdout,
            called_process_error.stderr,
        )
        return False
    return True


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
        return response.json()
    except JSONDecodeError as json_error:
        logging.error("Failed to parse response: %s", json_error)
        logging.error("First 1000 chars of response: %s", response.content[:1000])
        return {}


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


# def parse_config(config_to_parse: CONFIG_TYPING) -> CONFIG_TYPING:
#     """ loads the data file """
#     failed_to_load = False
#     for field in config_to_parse:
#         if field not in EXPECTED_CONFIG_FIELDS:
#             logging.warning("Found extra field in config: '%s' ignoring.", field)
#     for field in REQUIRED_CONFIG_FIELDS:
#         if field not in config_to_parse:
#             failed_to_load = True
#             logging.error("Failed to find %s in config, bailing.", field)
#     if failed_to_load:
#         sys.exit(1)
#     if config_to_parse["source"].startswith("http"):
#         config_to_parse["download_method"] = download_with_requests
#     elif config_to_parse["source"].startswith("s3:"):
#         config_to_parse["download_method"] = download_with_s3
#     else:
#         config_to_parse["download_method"] = sys.exit
#         raise UnsupportedSourceType(
#             f"Can't handle this: {config_to_parse.get('source')!r}"
#         )

#     for field, value in CONFIG_DEFAULTS:
#         if field not in config_to_parse:
#             config_to_parse[field] = value  # type: ignore
#             logging.debug("Setting default: %s=%s", field, value)

#     return config_to_parse


def download_and_ban(config_object):
    """ main action activity """

    if "download_method" in config_object:
        data: dict = config_object["download_method"](config_object)

    for item in data:
        if "--dryrun" not in sys.argv:
            jail = item.get(config_object["jail_field"])
            target = item.get(config_object["jail_target"])
            if not (jail and target):
                logging.error("Couldn't find jail and target in object: %s", item)
                continue
            ban_action(config_object["fail2ban_client"], jail, target)

def cli():
    """ main CLI thingie """

    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            f"""Usage: {os.path.basename(__file__)} [OPTIONS]

    Options:
    --dryrun         Test config/pulling data but don't make changes.
    --oneshot        Run this once and exit.
    -h, --help       Show this message and exit.
    """
        )
        sys.exit()

    # MAIN BIT
    config: Optional[CONFIG_TYPING] = load_config()
    if not config:
        config_files_joined = ",".join(CONFIG_FILES)
        logging.error(
            "Failed to find/load config file, looked in %s", config_files_joined
        )
        sys.exit(1)

    logging.debug(
        "Config: %s", json.dumps(config, indent=4, ensure_ascii=False, default=str)
    )

    config = ConfigFile.parse_file(load_config())

    logging.debug(
        json.dumps(
            config,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )

    download_and_ban(config)

    if "--oneshot" not in sys.argv and "--dryrun" not in sys.argv:
        logging.info("Running every %s minutes", config["schedule_mins"])
        schedule.every(config["schedule_mins"]).minutes.do(download_and_ban, config)
        while True:
            schedule.run_pending()
            sleep(10)


if __name__ == "__main__":
    cli()
