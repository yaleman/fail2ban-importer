#!/usr/bin/env python3

""" loads things from s3 or an s3-like thing, or maybe just https """

import json

import logging
import os
from time import sleep

import click
import schedule # type: ignore

from . import download_and_ban, downloaders
from .fail2ban_types import ConfigFile
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
