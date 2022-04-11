#!/usr/bin/env python3

""" loads things from s3 or an s3-like thing, or maybe just https """

# TODO: allow-listing

import json

import logging
import os
import subprocess
from time import sleep
from typing import Any

import click
import schedule

from . import downloaders
from .fail2ban_types import ConfigFile, Fail2BanData
from .utils import load_config

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

def download_and_ban(
    logging_module: logging.Logger,
    download_module: Any,
    config_object: ConfigFile,
    ) -> None:
    """ download and ban bit """
    data: Fail2BanData = download_module.download()
    if data is None:
        logging_module.error("Failed to get response from downloader...")
    if config_object.dryrun:
        logging_module.info(
            "I'd totally be banning %s in jail %s right now, else I'm in dry-run mode!",
            element.ip,
            config_object.fail2ban_jail,
        )
        return

    for element in data.data:
        ban_action(
            config_object.fail2ban_client,
            config_object.fail2ban_jail,
            element.ip,
        )

@click.command()
@click.option("--dryrun", "-n", is_flag=True, default=False, help="Make no changes, just test download and parse")
@click.option("--oneshot", "-o", is_flag=True, default=False)
def cli(
    dryrun: bool=False,
    oneshot: bool=False,
    ) -> None:
    """ main CLI thingie """

    config = ConfigFile.parse_obj(load_config())
    config.dryrun = dryrun
    config.oneshot = oneshot

    logger = logging.getLogger()
    logger.setLevel(level=getattr(logging, config.log_level))
    logger.debug(
        "Config: %s", json.dumps(config, indent=4, ensure_ascii=False, default=str)
    )

    download_module = getattr(downloaders,config.download_module)

    download_and_ban(logger, download_module, config)

    if not oneshot:
        logging.info("Running every %s minutes", config.schedule_mins)
        schedule.every(
            config.schedule_mins).minutes.do(
                download_and_ban,
                logger,
                download_module,
                config,
                )
        while True:
            schedule.run_pending()
            sleep(10)


if __name__ == "__main__":
    cli()
