""" downloader submodule for fail2ban-importer """

from . import http
from . import s3

__all__ = [
    "http",
    "s3",
]
