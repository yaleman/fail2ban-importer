"""" tests http pulls """

import json
from pathlib import Path

import fail2ban_importer.downloaders.http




def test_http_importer(tmp_path: Path) -> None:
    """ testing http importer """

    config_file = {
    "source" : "https://raw.githubusercontent.com/yaleman/fail2ban-importer/main/example.json"
    }

    config_path = tmp_path / "hello.txt"
    config_path.write_text(json.dumps(config_file))

    result =fail2ban_importer.downloaders.http.download(str(config_path))

    assert result is not None
    assert result.data[0].ip == "192.168.255.255"
