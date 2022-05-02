#!/usr/bin/env python3

""" loads things from s3 or an s3-like thing, or maybe just https """

import json
import logging
from time import sleep
from typing import Optional

import click
import schedule # type: ignore

from . import download_and_ban, downloaders, setup_logging
from .fail2ban_types import ConfigFile
from .utils import load_config

@click.command()
@click.option("--dryrun", "-n", is_flag=True, default=False, help="Make no changes, just test download and parse")
@click.option("--oneshot", "-o", is_flag=True, default=False)
@click.option("--debug", "-d", is_flag=True, default=False)
@click.option("--config-file", "-c", help="Specify the configuration file path.")
def cli(
    dryrun: bool=False,
    oneshot: bool=False,
    config_file: Optional[str]=None,
    debug: bool=False
    ) -> None:
    """ main CLI thingie """

    config = ConfigFile.parse_obj(load_config(config_file=config_file))
    config.dryrun = dryrun
    config.oneshot = oneshot

    if debug:
        config.log_level="DEBUG"
    setup_logging(config.log_level)

    logging.debug(
        "Config: %s", json.dumps(config, indent=4, ensure_ascii=False, default=str)
    )
    download_module = getattr(downloaders,config.download_module)

    download_and_ban(download_module, config_file, config)

    if not oneshot:
        logging.info("Running every %s minutes", config.schedule_mins)
        schedule.every(
            config.schedule_mins).minutes.do(
                download_and_ban,
                download_module,
                config,
                )
        while True:
            schedule.run_pending()
            sleep(10)


if __name__ == "__main__":
    cli()
