"""Единая точка входа: python -m sysadmin_toolkit <команда> [параметры]."""

import argparse
import logging
import sys
from pathlib import Path

from . import __version__, backup, ping_check, sysinfo


def setup_logging(log_file: str | None):
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def cmd_ping(args) -> int:
    targets = [ping_check.parse_target(h) for h in args.hosts]
    if args.file:
        targets += ping_check.load_targets(args.file)
    targets = [t for t in targets if t]
    if not targets:
        print("Не указаны хосты. Пример: ping 8.8.8.8 ya.ru:443 или --file hosts.txt")
        return 2
    results = ping_check.check_targets(targets, timeout=args.timeout)
    print(ping_check.format_results(results))
    # код возврата 1, если хоть один хост недоступен — удобно для скриптов
    return 0 if all(r.alive for r in results) else 1


def cmd_sysinfo(args) -> int:
    info = sysinfo.collect()
    text = sysinfo.to_json(info) if args.json else sysinfo.format_report(info)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Отчёт сохранён в {args.output}")
    else:
        print(text)
    return 0


def cmd_backup(args) -> int:
    try:
        if args.every:
            backup.run_scheduled(args.source, args.dest, args.every, args.keep, args.exclude)
        else:
            backup.make_backup(args.source, args.dest, args.exclude)
            backup.rotate(args.dest, Path(args.source).resolve().name, args.keep)
    except (NotADirectoryError, ValueError) as e:
        logging.error(e)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sysadmin_toolkit",
        description="Набор утилит системного администратора",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--log", metavar="ФАЙЛ", help="дополнительно писать лог в файл")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ping", help="проверить доступность хостов")
    p.add_argument("hosts", nargs="*", help="хосты: 8.8.8.8 или ya.ru:443")
    p.add_argument("-f", "--file", help="файл со списком хостов")
    p.add_argument("-t", "--timeout", type=int, default=2, help="таймаут, сек (2)")
    p.set_defaults(func=cmd_ping)

    s = sub.add_parser("sysinfo", help="показать информацию о системе")
    s.add_argument("--json", action="store_true", help="вывод в формате JSON")
    s.add_argument("-o", "--output", help="сохранить отчёт в файл")
    s.set_defaults(func=cmd_sysinfo)

    b = sub.add_parser("backup", help="сделать резервную копию папки")
    b.add_argument("source", help="какую папку копировать")
    b.add_argument("dest", help="куда класть архивы")
    b.add_argument("-k", "--keep", type=int, default=5, help="сколько архивов хранить (5)")
    b.add_argument("-e", "--exclude", action="append", default=[],
                   help="исключить по шаблону, например -e '*.tmp' -e __pycache__")
    b.add_argument("--every", type=float, metavar="МИН",
                   help="повторять каждые N минут (расписание)")
    b.set_defaults(func=cmd_backup)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(args.log)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
