""" from """

from json.decoder import JSONDecodeError
import logging
from typing import Optional

import pydantic.error_wrappers
from requests import Session
import requests.exceptions

from ..fail2ban_types import ConfigFileHTTP, Fail2BanData
from ..utils import load_config


def download(config_path: Optional[str]) -> Optional[Fail2BanData]:
    """downloads the source file using the requests library"""

    config = ConfigFileHTTP.model_validate(load_config(config_path))
    logging.debug("Download config: %s", config.model_dump_json())

    session = Session()

    if config.proxies:
        logging.debug("Setting proxies to %s", config.proxies)
        session.proxies = config.proxies

    try:
        logging.debug("Downloading from %s", config.source)
        response = session.request(
            url=config.source,
            method=config.http_method,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_error:
        logging.error(
            "Failed to download from '%s': %s",
            config.source,
            http_error,
        )

    try:
        data = Fail2BanData(data=response.json())
        logging.debug(data.model_dump())
        if data is None:
            return None
        for element in data.data:
            logging.debug(element.jail)
    except JSONDecodeError as json_error:
        logging.error("Failed to parse response: %s", json_error)
        logging.error("First 1000 chars of response: %s", response.content[:1000])
        return None
    except pydantic.error_wrappers.ValidationError as validation_error:
        logging.error("Failed to parse response: %s", validation_error)
        logging.error("First 1000 chars of response: %s", response.content[:1000])
        return None
    return data
