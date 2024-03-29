""" s3 downloader """

import json
from json.decoder import JSONDecodeError
import logging
import os
import sys
from typing import Optional
from urllib.parse import urlparse

import boto3
import botocore.exceptions
import pydantic.error_wrappers

from ..utils import load_config
from ..fail2ban_types import ConfigFileS3, Fail2BanData


def download(
    config_file: Optional[str],
) -> Optional[Fail2BanData]:
    """downloads the source file using the requests library"""

    config = ConfigFileS3.model_validate(load_config(config_file))
    logging.debug(config.model_dump_json())

    # try and pull apart the s3 url
    try:
        parsed_s3_url = urlparse(config.source)
        logging.debug(parsed_s3_url)
    except ValueError as url_parser_error:
        logging.error(
            "Failed to parse s3 url  '%s': %s",
            config.source,
            url_parser_error,
        )
        sys.exit(1)

    for var in [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_CONFIG_FILE",
        "AWS_PROFILE",
    ]:
        if not os.getenv(var, None):
            if hasattr(config, var) and getattr(config, var) is not None:
                os.environ[var] = getattr(config, var)

    logging.debug("Creating s3 client")
    s3_config = None
    if config.s3_minio or config.s3_v4:
        s3_config = boto3.session.Config(signature_version="v4")  # type: ignore

    if config.s3_endpoint:
        s3_resource = boto3.resource(
            "s3",
            endpoint_url=config.s3_endpoint,
            config=s3_config,
        )
    else:
        s3_resource = boto3.resource("s3", config=s3_config)

    logging.debug("Getting object")

    try:
        s3_object = s3_resource.Object(
            bucket_name=parsed_s3_url.netloc,
            key=str(parsed_s3_url.path).lstrip("/"),
        )
        contents = s3_object.get()
    except botocore.exceptions.ClientError as client_error:
        logging.error("botocore.exceptions.ClientError: %s", client_error)
        return None
    try:
        if "Body" not in contents:
            raise ValueError("Failed to get a Body from S3 Call")

        content = json.loads(contents["Body"].read().decode("utf-8"))
        return Fail2BanData(data=content)
    except JSONDecodeError as json_error:
        logging.error("Failed to parse response: %s", json_error)
        logging.error("First 1000 chars of response: %s", content[:1000])
    except pydantic.error_wrappers.ValidationError as validation_error:
        logging.error("Failed to parse response from s3: %s", validation_error)
        logging.error("First 1000 chars of response: %s", content[:1000])
    return None
