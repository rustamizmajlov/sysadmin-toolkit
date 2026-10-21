import zipfile

import pytest

from sysadmin_toolkit import backup


@pytest.fixture
def project(tmp_path):
    src = tmp_path / "docs"
    (src / "sub").mkdir(parents=True)
    (src / "a.txt").write_text("hello")
    (src / "sub" / "b.txt").write_text("world")
    (src / "temp.tmp").write_text("мусор", encoding="utf-8")
    return src


def test_backup_creates_zip_with_files(project, tmp_path):
    archive = backup.make_backup(project, tmp_path / "out")
    assert archive.exists()
    names = zipfile.ZipFile(archive).namelist()
    assert "docs/a.txt" in names
    assert "docs/sub/b.txt" in names


def test_backup_exclude(project, tmp_path):
    archive = backup.make_backup(project, tmp_path / "out", exclude=["*.tmp"])
    assert "docs/temp.tmp" not in zipfile.ZipFile(archive).namelist()


def test_backup_missing_source(tmp_path):
    with pytest.raises(NotADirectoryError):
        backup.make_backup(tmp_path / "nope", tmp_path / "out")


def test_backup_dest_inside_source_forbidden(project):
    with pytest.raises(ValueError):
        backup.make_backup(project, project / "backups")


def test_rotate_keeps_last(tmp_path):
    for i in range(5):
        (tmp_path / f"backup_docs_2026-01-0{i + 1}_00-00-00.zip").write_text("x")
    removed = backup.rotate(tmp_path, "docs", keep=2)
    left = sorted(p.name for p in tmp_path.glob("*.zip"))
    assert len(removed) == 3
    assert left == ["backup_docs_2026-01-04_00-00-00.zip",
                    "backup_docs_2026-01-05_00-00-00.zip"]


def test_scheduled_runs_limited(project, tmp_path, monkeypatch):
    monkeypatch.setattr(backup.time, "sleep", lambda s: None)  # не ждём по-настоящему
    monkeypatch.setattr(backup, "make_backup", lambda *a, **k: None)
    calls = []
    monkeypatch.setattr(backup, "rotate", lambda *a: calls.append(a))
    backup.run_scheduled(project, tmp_path / "out", every_minutes=1, keep=3, max_runs=3)
    assert len(calls) == 3
