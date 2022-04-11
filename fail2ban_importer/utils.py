""" utilities """

import json
import logging
from pathlib import Path
from typing import Any, Dict

def load_config(
    logger: logging.Logger=logging.getLogger("load_config"),
    ) -> Dict[str, Any]:
    """ loads config """

    for test_path in [
        "./fail2ban-importer.json",
        "/etc/fail2ban-importer.json",
        "~/.config/fail2ban-importer.json",
    ]:
        filepath = Path(test_path).expanduser().resolve()
        if not filepath.exists():
            logger.debug("%s not found", filepath)
            continue
        config_file: Dict[str, Any] = json.load(filepath.open(encoding="utf-8"))
        return config_file
    raise FileNotFoundError("Couldn't find a configuration file...")
