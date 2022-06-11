"""" tests http pulls """

import json
from pathlib import Path

import fail2ban_importer.downloaders.http




def test_http_importer(tmp_path: Path) -> None:
    """ testing http importer """

    config_file = {
    "source" : "https://raw.githubusercontent.com/yaleman/fail2ban-importer/main/example.json"
    }

    p = tmp_path / "hello.txt"
    p.write_text(json.dumps(config_file))

    result =fail2ban_importer.downloaders.http.download(str(p))

    assert result.data[0].ip == "192.168.255.255"

