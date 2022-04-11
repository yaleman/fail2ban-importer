""" Downloads JSON-encoded lists from s3 or HTTPS endpoints and bans them

"""

import logging
import subprocess
from typing import Any
from .fail2ban_types import ConfigFile, Fail2BanData


def ban_action(
    client_command: str,
    logger: logging.Logger,
    jail_name: str,
    target_ip: str,
    ) -> bool:
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
        stdout = result.stdout.decode("utf-8").strip()
        if stdout == "1":
            logger.info("Banned %s", target_ip)
            return True
        if stdout == "0":
            logger.info("%s already in %s", target_ip, jail_name)
            return False
        logger.error("Unexpected output: %s", stdout)
    except subprocess.CalledProcessError as called_process_error:
        command_joined = " ".join(command)
        logger.error(
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

    for element in data.data:

        if element.ip in config_object.ignore_list:
            logging_module.debug("Skipping %s, in ignore list", element.ip)
            continue

        if config_object.dryrun:
            logging_module.info(
                "I'd totally be banning %s in jail %s right now, else I'm in dry-run mode!",
                element.ip,
                config_object.fail2ban_jail,
            )
            continue

        ban_action(
            client_command=config_object.fail2ban_client,
            logger=logging_module,
            jail_name=config_object.fail2ban_jail,
            target_ip=element.ip,
        )

def setup_logging(log_level:str) -> logging.Logger:
    """ sets up logging """
    logger = logging.getLogger()
    if hasattr(logging, log_level.upper()):
        logger.setLevel(level=getattr(logging, log_level.upper()))
    else:
        logger.error("Invalid log level set, defaulting to debug: %s", log_level.upper())
        logger.setLevel(level=logging.DEBUG)
    return logger
