""" types """

from typing import Dict, List, Optional

from pydantic import BaseModel


class ConfigFile(BaseModel):
    """ config file for fail2ban-importer """
    download_module: str = "http"
    source: str = "https://raw.githubusercontent.com/yaleman/fail2ban-importer/main/example.json"
    log_level: str = "INFO"
    fail2ban_client: str = "fail2ban-client"
    fail2ban_jail: str = "fail2ban-importer"
    schedule_mins: int = 15
    dryrun: bool = False
    oneshot: bool = False
    ignore_list: List[str] = [ "127.0.0.1", ]


class ConfigFileHTTP(ConfigFile):
    """ config file for HTTP sources """
    username: Optional[str]
    password: Optional[str]

    http_method: str = "get"

    proxies: Optional[Dict[str,str]]

    class Config: # pylint: disable=too-few-public-methods
        """ config class """
        arbitrary_types_allowed = True

class ConfigFileS3(ConfigFile):
    """ Extension to the config file, supporting S3 options """
    s3_minio: bool=False
    s3_v4: bool=False
    s3_endpoint: Optional[str]
    AWS_ACCESS_KEY_ID: Optional[str]
    AWS_SECRET_ACCESS_KEY: Optional[str]
    AWS_CONFIG_FILE: Optional[str]
    AWS_PROFILE: Optional[str]

    # class Config: # pylint: disable=too-few-public-methods
    #     """ config class """
    #     arbitrary_types_allowed = True

class Fail2BanTarget(BaseModel):
    """ individual/host """
    ip: str
    jail: str

class Fail2BanData(BaseModel):
    """ data """
    data: List[Fail2BanTarget]
