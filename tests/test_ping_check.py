import socket
from unittest import mock

from sysadmin_toolkit import ping_check


def test_parse_target_plain_host():
    assert ping_check.parse_target("8.8.8.8") == ("8.8.8.8", None)


def test_parse_target_with_port():
    assert ping_check.parse_target("ya.ru:443") == ("ya.ru", 443)


def test_parse_target_skips_comments_and_empty():
    assert ping_check.parse_target("# комментарий") is None
    assert ping_check.parse_target("   ") is None
    assert ping_check.parse_target("1.1.1.1  # DNS") == ("1.1.1.1", None)


def test_build_ping_command_linux():
    with mock.patch("platform.system", return_value="Linux"):
        assert ping_check.build_ping_command("h")[:3] == ["ping", "-c", "1"]


def test_build_ping_command_windows():
    with mock.patch("platform.system", return_value="Windows"):
        assert ping_check.build_ping_command("h")[:3] == ["ping", "-n", "1"]


def test_tcp_port_open():
    # поднимаем локальный сервер, чтобы тест не зависел от интернета
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    try:
        result = ping_check.check_tcp_port("127.0.0.1", port)
        assert result.alive
        assert result.method == f"tcp:{port}"
    finally:
        server.close()


def test_tcp_port_closed():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # порт теперь точно никто не слушает
    assert not ping_check.check_tcp_port("127.0.0.1", port, timeout=1).alive


def test_load_targets(tmp_path):
    f = tmp_path / "hosts.txt"
    f.write_text("# мои хосты\n8.8.8.8\n\nya.ru:443\n", encoding="utf-8")
    assert ping_check.load_targets(str(f)) == [("8.8.8.8", None), ("ya.ru", 443)]


def test_format_results_counts_up():
    results = [
        ping_check.HostResult("a", True, 10.0, "ping"),
        ping_check.HostResult("b", False, None, "ping"),
    ]
    assert "Доступно: 1 из 2" in ping_check.format_results(results)
