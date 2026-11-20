from __future__ import annotations


def probe_ssh(
    host: str,
    port: int,
    username: str,
    password: str,
    *,
    timeout: float = 8.0,
) -> tuple[bool, str]:
    """尝试 SSH 密码登录。成功返回 (True, '')，失败返回 (False, 原因)。"""
    if not host or not username or not password:
        return False, "缺少主机地址或 SSH 账号密码"
    try:
        import paramiko
    except ImportError:
        return False, "服务端未安装 paramiko，无法校验 SSH"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=int(port or 22),
            username=username,
            password=password,
            timeout=timeout,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=timeout,
            auth_timeout=timeout,
        )
        # 轻量探活
        client.exec_command("echo ok", timeout=timeout)
        return True, ""
    except Exception as exc:  # noqa: BLE001 - 需要把连通失败原因回给前端
        return False, f"SSH 校验失败: {exc}"
    finally:
        client.close()
