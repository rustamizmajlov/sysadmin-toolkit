import json

from sysadmin_toolkit import sysinfo


def test_bytes_to_human():
    assert sysinfo.bytes_to_human(512) == "512.0 Б"
    assert sysinfo.bytes_to_human(1536) == "1.5 КБ"
    assert sysinfo.bytes_to_human(1024 ** 3) == "1.0 ГБ"


def test_collect_has_main_sections():
    info = sysinfo.collect()
    for key in ("hostname", "os", "uptime", "cpu", "memory", "disks", "network"):
        assert key in info
    assert 0 <= info["memory"]["percent"] <= 100


def test_report_and_json():
    info = sysinfo.collect()
    assert info["hostname"] in sysinfo.format_report(info)
    assert json.loads(sysinfo.to_json(info))["hostname"] == info["hostname"]
