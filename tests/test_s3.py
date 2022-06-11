"""" tests http pulls """

import os
import json
from pathlib import Path

import pytest

import fail2ban_importer.downloaders.s3




def test_http_importer(tmp_path: Path) -> None:
    """ testing http importer """

    config_file = {
        "source" : "s3://fail2ban-importer-test/example.json"
    }

    config_path = tmp_path / "hello.txt"
    config_path.write_text(json.dumps(config_file))

    if( os.getenv("AWS_PROFILE") or (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))):

        result = fail2ban_importer.downloaders.s3.download(str(config_path))

        assert result is not None
        assert result.data[0].ip == "192.168.255.255"
    else:
        pytest.skip()
