from sysadmin_toolkit import cli


def test_sysinfo_command(capsys):
    assert cli.main(["sysinfo"]) == 0
    assert "Отчёт о системе" in capsys.readouterr().out


def test_ping_without_hosts_returns_2(capsys):
    assert cli.main(["ping"]) == 2


def test_backup_command(tmp_path):
    src = tmp_path / "data"
    src.mkdir()
    (src / "f.txt").write_text("1")
    assert cli.main(["backup", str(src), str(tmp_path / "out")]) == 0
    assert len(list((tmp_path / "out").glob("*.zip"))) == 1


def test_backup_bad_source(tmp_path):
    assert cli.main(["backup", str(tmp_path / "nope"), str(tmp_path / "out")]) == 2
