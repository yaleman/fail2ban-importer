""" utilities """

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional

CONFIG_PATHS = [
    "./fail2ban-importer.json",
    "/etc/fail2ban-importer.json",
    "~/.config/fail2ban-importer.json",
]

def load_config(
    config_file: Optional[str],
    ) -> Dict[str, Any]:
    """ loads config """

    test_paths = CONFIG_PATHS
    if config_file is not None:
        logging.debug("Using configured file %s", config_file)
        filepath = Path(config_file).expanduser().resolve()
        if not filepath.exists():
            logging.error("Couldn't find configured path: %s", filepath)
            sys.exit(1)
        test_paths = [config_file]
    logging.debug("test_paths: %s", test_paths)
    for test_path in test_paths:
        filepath = Path(test_path).expanduser().resolve()
        if not filepath.exists():
            logging.debug("%s not found", filepath)
            continue
        logging.debug("Using config file: %s", filepath)
        try:
            config_contents: Dict[str, Any] = json.load(filepath.open(encoding="utf-8"))
        except json.JSONDecodeError as json_error:
            logging.error("Failed to parse config file %s: %s", filepath, json_error)
            sys.exit(1)
        return config_contents
    return {}
    #raise FileNotFoundError("Couldn't find a configuration file...")
