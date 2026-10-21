"""Проверка доступности хостов: ping и проверка TCP-порта."""

import logging
import platform
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class HostResult:
    host: str
    alive: bool
    latency_ms: float | None  # время ответа, если хост доступен
    method: str  # "ping" или "tcp:<порт>"


def build_ping_command(host: str, count: int = 1, timeout: int = 2) -> list[str]:
    """Собирает команду ping с учётом ОС (у Windows другие ключи)."""
    if platform.system().lower() == "windows":
        return ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    return ["ping", "-c", str(count), "-W", str(timeout), host]


def ping_host(host: str, timeout: int = 2) -> HostResult:
    """Пингует хост системной утилитой ping."""
    start = time.perf_counter()
    try:
        result = subprocess.run(
            build_ping_command(host, timeout=timeout),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 2,
        )
        alive = result.returncode == 0
    except subprocess.TimeoutExpired:
        alive = False
    except FileNotFoundError:
        log.warning("Утилита ping не найдена в системе — используйте проверку порта host:port")
        alive = False
    elapsed = (time.perf_counter() - start) * 1000
    return HostResult(host, alive, round(elapsed, 1) if alive else None, "ping")


def check_tcp_port(host: str, port: int, timeout: float = 2.0) -> HostResult:
    """Проверяет, открыт ли TCP-порт (полезно, когда ICMP запрещён)."""
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000
            return HostResult(host, True, round(elapsed, 1), f"tcp:{port}")
    except OSError:
        return HostResult(host, False, None, f"tcp:{port}")


def parse_target(line: str) -> tuple[str, int | None] | None:
    """Разбирает строку 'host' или 'host:port'. Пустые строки и # — комментарии."""
    line = line.split("#", 1)[0].strip()
    if not line:
        return None
    if ":" in line:
        host, port = line.rsplit(":", 1)
        if port.isdigit():
            return host.strip(), int(port)
    return line, None


def load_targets(path: str) -> list[tuple[str, int | None]]:
    """Читает список хостов из файла."""
    with open(path, encoding="utf-8") as f:
        return [t for t in (parse_target(line) for line in f) if t is not None]


def check_targets(targets, timeout: int = 2, workers: int = 10) -> list[HostResult]:
    """Проверяет все цели параллельно, порядок результатов сохраняется."""

    def check(target):
        host, port = target
        return check_tcp_port(host, port, timeout) if port else ping_host(host, timeout)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(check, targets))


def format_results(results: list[HostResult]) -> str:
    """Делает аккуратную таблицу для вывода в консоль."""
    lines = [f"{'ХОСТ':<30} {'МЕТОД':<10} {'СТАТУС':<8} {'ВРЕМЯ':>9}", "-" * 60]
    for r in results:
        status = "UP" if r.alive else "DOWN"
        latency = f"{r.latency_ms} мс" if r.latency_ms is not None else "—"
        lines.append(f"{r.host:<30} {r.method:<10} {status:<8} {latency:>9}")
    up = sum(r.alive for r in results)
    lines.append("-" * 60)
    lines.append(f"Доступно: {up} из {len(results)}")
    return "\n".join(lines)
