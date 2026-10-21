"""Резервное копирование папки в zip-архив с ротацией старых копий."""

import datetime
import fnmatch
import logging
import time
import zipfile
from pathlib import Path

log = logging.getLogger(__name__)

ARCHIVE_PREFIX = "backup_"


def is_excluded(path: Path, patterns: list[str]) -> bool:
    """True, если файл или любая папка на пути подходит под шаблон исключения."""
    return any(fnmatch.fnmatch(part, p) for part in path.parts for p in patterns)


def make_backup(source: str, dest: str, exclude: list[str] | None = None) -> Path:
    """Упаковывает папку source в dest/backup_<имя>_<дата>.zip."""
    src, dst = Path(source).resolve(), Path(dest).resolve()
    if not src.is_dir():
        raise NotADirectoryError(f"Папка не найдена: {src}")
    if dst == src or src in dst.parents:
        raise ValueError("Папку для бэкапов нельзя класть внутрь копируемой папки")
    dst.mkdir(parents=True, exist_ok=True)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive = dst / f"{ARCHIVE_PREFIX}{src.name}_{stamp}.zip"
    exclude = exclude or []

    count = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(src.rglob("*")):
            rel = file.relative_to(src)
            if file.is_file() and not is_excluded(rel, exclude):
                zf.write(file, Path(src.name) / rel)
                count += 1

    log.info("Создан архив %s (%d файлов)", archive.name, count)
    return archive


def rotate(dest: str, source_name: str, keep: int) -> list[Path]:
    """Оставляет только keep последних архивов, остальные удаляет."""
    archives = sorted(Path(dest).glob(f"{ARCHIVE_PREFIX}{source_name}_*.zip"))
    removed = archives[:-keep] if keep > 0 else []
    for old in removed:
        old.unlink()
        log.info("Удалён старый архив %s", old.name)
    return removed


def run_scheduled(source: str, dest: str, every_minutes: float, keep: int,
                  exclude: list[str] | None = None, max_runs: int | None = None):
    """Делает бэкап каждые N минут. Остановить — Ctrl+C."""
    runs = 0
    log.info("Расписание: каждые %s мин. Для остановки нажмите Ctrl+C", every_minutes)
    try:
        while max_runs is None or runs < max_runs:
            make_backup(source, dest, exclude)
            rotate(dest, Path(source).resolve().name, keep)
            runs += 1
            if max_runs is None or runs < max_runs:
                time.sleep(every_minutes * 60)
    except KeyboardInterrupt:
        log.info("Остановлено пользователем")
