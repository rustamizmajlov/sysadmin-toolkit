# 🛠 Sysadmin Toolkit

![tests](https://github.com/<ваш-логин>/sysadmin-toolkit/actions/workflows/tests.yml/badge.svg)

Набор консольных утилит для системного администратора на Python. Все утилиты работают на **Windows и Linux** и запускаются одной командой.

| Команда   | Что делает                                                        |
|-----------|-------------------------------------------------------------------|
| `ping`    | Проверяет доступность хостов (ICMP ping или TCP-порт), параллельно |
| `sysinfo` | Собирает отчёт о системе: ОС, CPU, RAM, диски, сеть, аптайм        |
| `backup`  | Архивирует папку в zip, хранит N последних копий, умеет по расписанию |

## Установка

```bash
git clone https://github.com/<ваш-логин>/sysadmin-toolkit.git
cd sysadmin-toolkit
python -m venv venv
# Windows: venv\Scripts\activate   |   Linux: source venv/bin/activate
pip install -r requirements.txt
```

Нужен Python 3.10+.

## Использование

### Проверка доступности хостов

```bash
python -m sysadmin_toolkit ping 8.8.8.8 ya.ru:443
python -m sysadmin_toolkit ping --file hosts.example.txt
```

```
ХОСТ                           МЕТОД      СТАТУС       ВРЕМЯ
------------------------------------------------------------
8.8.8.8                        ping       UP         24.3 мс
ya.ru                          tcp:443    UP         18.7 мс
192.168.1.50                   ping       DOWN             —
------------------------------------------------------------
Доступно: 2 из 3
```

- `хост` проверяется через ping, `хост:порт` — через TCP-подключение (удобно, если ICMP закрыт файрволом).
- Хосты проверяются параллельно, поэтому даже длинный список проходит быстро.
- Код возврата `1`, если хотя бы один хост недоступен, поэтому команду можно встраивать в другие скрипты.

### Информация о системе

```bash
python -m sysadmin_toolkit sysinfo                  # отчёт в консоль
python -m sysadmin_toolkit sysinfo --json -o report.json
```

Диски, заполненные на 90% и больше, помечаются предупреждением.

### Резервное копирование

```bash
# разовый бэкап, хранить 5 последних архивов
python -m sysadmin_toolkit backup ./documents ./backups

# исключить временные файлы и хранить только 3 копии
python -m sysadmin_toolkit backup ./project ./backups -e "*.tmp" -e __pycache__ -k 3

# бэкап каждые 60 минут с записью лога в файл
python -m sysadmin_toolkit --log backup.log backup ./documents ./backups --every 60
```

Архивы называются `backup_<папка>_<дата_время>.zip`. Самые старые удаляются автоматически.

#### Запуск по расписанию средствами ОС

Вместо `--every` можно поручить расписание системе:

**Linux (cron)**: каждый день в 03:00:
```
0 3 * * * cd /path/to/sysadmin-toolkit && python3 -m sysadmin_toolkit --log backup.log backup /home/user/docs /mnt/backups
```

**Windows (Планировщик заданий)**:
```
schtasks /create /tn "DailyBackup" /sc daily /st 03:00 /tr "python -m sysadmin_toolkit backup C:\Docs D:\Backups"
```

## Тесты

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

Тесты автоматически запускаются через GitHub Actions на Ubuntu и Windows при каждом push.

## Структура проекта

```
sysadmin-toolkit/
├── sysadmin_toolkit/
│   ├── cli.py          # разбор аргументов, общий вход
│   ├── ping_check.py   # проверка доступности хостов
│   ├── sysinfo.py      # сбор информации о системе
│   └── backup.py       # резервное копирование и ротация
├── tests/              # тесты pytest
├── hosts.example.txt   # пример списка хостов
└── .github/workflows/  # CI
```

## Идеи для развития

- [ ] Уведомление в Telegram, если хост упал
- [ ] Мониторинг в цикле с историей в CSV
- [ ] Проверка срока действия SSL-сертификатов
- [ ] Бэкап на удалённый сервер по SFTP

## Автор

Рустам Измайлов — студент направления «Программная инженерия и ИТ».

## Лицензия

MIT
