""" Downloads JSON-encoded lists from s3 or HTTPS endpoints and bans them

"""

import logging
import subprocess
from typing import Any, Optional
from .fail2ban_types import ConfigFile, Fail2BanData


def ban_action(
    client_command: str,
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
            logging.info("Banned %s", target_ip)
            return True
        if stdout == "0":
            logging.info("%s already in %s", target_ip, jail_name)
            return False
        logging.error("Unexpected output: %s", stdout)
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
    download_module: Any,
    config_path: Optional[str],
    config_object: ConfigFile,
    ) -> None:
    """ download and ban bit """
    data: Fail2BanData = download_module.download(config_path)
    if data is None:
        logging.error("Failed to get response from downloader...")
        return
    for element in data.data:

        if element.ip in config_object.ignore_list:
            logging.debug("Skipping %s, in ignore list", element.ip)
            continue

        if config_object.dryrun:
            logging.info(
                "I'd totally be banning %s in jail %s right now, but I'm in dry-run mode!",
                element.ip,
                config_object.fail2ban_jail,
            )
            continue

        ban_action(
            client_command=config_object.fail2ban_client,
            jail_name=config_object.fail2ban_jail,
            target_ip=element.ip,
        )

def setup_logging(
    log_level:str,
    ) -> logging.Logger:
    """ sets up logging """
    logger = logging.getLogger()

    if hasattr(logging, log_level.upper()):
        logger.setLevel(level=getattr(logging, log_level.upper()))
    else:
        logging.error("Invalid log level set, defaulting to debug: %s", log_level.upper())
        logger.setLevel(level=logging.DEBUG)
    return logger
