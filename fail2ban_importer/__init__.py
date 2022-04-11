""" Downloads JSON-encoded lists from s3 or HTTPS endpoints and bans them

"""

import logging
import subprocess


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
        elif stdout == "0":
            logging.info("%s already in %s", target_ip, jail_name)
            return False
        else:
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
