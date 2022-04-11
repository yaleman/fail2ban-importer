""" Downloads JSON-encoded lists from s3 or HTTPS endpoints and bans them

"""

import logging
import subprocess


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
