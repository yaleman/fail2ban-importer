""" from """

from json.decoder import JSONDecodeError
import logging
from typing import Optional

import pydantic.error_wrappers
from requests import Session
import requests.exceptions

from ..fail2ban_types import ConfigFileHTTP, Fail2BanData
from ..utils import load_config

def download() -> Optional[Fail2BanData]:
    """ downloads the source file using the requests library """

    config = ConfigFileHTTP.parse_obj(load_config())

    logger = logging.getLogger("HTTP")
    if config.log_level in dir(logging):
        logger.setLevel(getattr(logging, config.log_level))
    else:
        raise ValueError(f"Invalid log level: {config.log_level}")
    logger.debug("Download config: %s", config.json())

    session = Session()

    if config.proxies:
        logger.debug("Setting proxies to %s", config.proxies)
        session.proxies = config.proxies

    try:
        logger.debug("Downloading from %s", config.source)
        response = session.request(
            url=config.source,
            method=config.http_method,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_error:
        logger.error(
            "Failed to download from '%s': %s",
            config.source,
            http_error,
            )

    try:
        data = Fail2BanData(data=response.json())
        logger.debug(data.dict())
        for element in data.data:
            logger.debug(element.jail)
    except JSONDecodeError as json_error:
        logging.error("Failed to parse response: %s", json_error)
        logging.error("First 1000 chars of response: %s", response.content[:1000])
        return None
    except pydantic.error_wrappers.ValidationError as validation_error:
        logging.error("Failed to parse response: %s", validation_error)
        logging.error("First 1000 chars of response: %s", response.content[:1000])
        return None
    return data
