"""Сбор информации о системе: ОС, процессор, память, диски, сеть."""

import datetime
import json
import platform
import socket

import psutil


def bytes_to_human(n: float) -> str:
    """Переводит байты в удобный вид: 1536 -> '1.5 КБ'."""
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} ПБ"


def get_uptime() -> str:
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.datetime.now() - boot
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    return f"{delta.days} д {hours % 24} ч {rem // 60} мин"


def collect() -> dict:
    """Собирает все данные в один словарь (его удобно сохранить в JSON)."""
    mem = psutil.virtual_memory()
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue  # например, пустой CD-привод в Windows
        disks.append({
            "mount": part.mountpoint,
            "fs": part.fstype,
            "total": bytes_to_human(usage.total),
            "used": bytes_to_human(usage.used),
            "percent": usage.percent,
        })

    interfaces = {}
    for name, addrs in psutil.net_if_addrs().items():
        ipv4 = [a.address for a in addrs if a.family == socket.AF_INET]
        if ipv4:
            interfaces[name] = ipv4

    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "uptime": get_uptime(),
        "cpu": {
            "model": platform.processor() or platform.machine(),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "load_percent": psutil.cpu_percent(interval=0.5),
        },
        "memory": {
            "total": bytes_to_human(mem.total),
            "used": bytes_to_human(mem.used),
            "percent": mem.percent,
        },
        "disks": disks,
        "network": interfaces,
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def format_report(info: dict) -> str:
    """Превращает словарь в читаемый текстовый отчёт."""
    cpu, mem = info["cpu"], info["memory"]
    lines = [
        f"=== Отчёт о системе: {info['hostname']} ===",
        f"ОС:         {info['os']}",
        f"Аптайм:     {info['uptime']}",
        f"Процессор:  {cpu['model']} ({cpu['cores_physical']} физ. / "
        f"{cpu['cores_logical']} лог. ядер), загрузка {cpu['load_percent']}%",
        f"Память:     {mem['used']} из {mem['total']} ({mem['percent']}%)",
        "Диски:",
    ]
    for d in info["disks"]:
        warn = "  <-- мало места!" if d["percent"] >= 90 else ""
        lines.append(f"  {d['mount']:<20} {d['used']:>10} / {d['total']:<10} "
                     f"({d['percent']}%){warn}")
    lines.append("Сеть:")
    for name, ips in info["network"].items():
        lines.append(f"  {name:<15} {', '.join(ips)}")
    lines.append(f"Собрано:    {info['collected_at']}")
    return "\n".join(lines)


def to_json(info: dict) -> str:
    return json.dumps(info, ensure_ascii=False, indent=2)
