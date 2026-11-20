from __future__ import annotations

import logging
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)
LogCallback = Callable[[str], None]


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class ComposeEngine:
    def __init__(self, docker_bin: str | None = None) -> None:
        self.docker_bin = docker_bin or settings.docker_bin

    def _run(
        self,
        args: list[str],
        cwd: Path | None = None,
        timeout: int | None = 600,
        on_line: LogCallback | None = None,
    ) -> CommandResult:
        cmd = [self.docker_bin, *args]
        logger.info("exec: %s (cwd=%s)", " ".join(cmd), cwd)
        try:
            if on_line is None:
                proc = subprocess.run(
                    cmd,
                    cwd=str(cwd) if cwd else None,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                return CommandResult(proc.returncode, proc.stdout or "", proc.stderr or "")

            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            chunks: list[str] = []
            assert proc.stdout is not None
            for line in proc.stdout:
                text = line.rstrip("\n")
                chunks.append(text)
                on_line(text)
            try:
                returncode = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                on_line("ERROR: command timeout")
                return CommandResult(124, "\n".join(chunks), "timeout")
            return CommandResult(returncode, "\n".join(chunks), "")
        except FileNotFoundError:
            msg = f"docker binary not found: {self.docker_bin}"
            if on_line:
                on_line(msg)
            return CommandResult(127, "", msg)
        except subprocess.TimeoutExpired as exc:
            out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            err = (exc.stderr or "") if isinstance(exc.stderr, str) else "timeout"
            return CommandResult(124, out, err)

    def compose_pull(
        self,
        project: str,
        compose_file: Path,
        work_dir: Path,
        on_line: LogCallback | None = None,
    ) -> CommandResult:
        return self._run(
            ["compose", "-p", project, "-f", str(compose_file), "pull"],
            cwd=work_dir,
            timeout=1800,
            on_line=on_line,
        )

    def compose_up(
        self,
        project: str,
        compose_file: Path,
        work_dir: Path,
        on_line: LogCallback | None = None,
    ) -> CommandResult:
        return self._run(
            [
                "compose",
                "-p",
                project,
                "-f",
                str(compose_file),
                "up",
                "-d",
                "--remove-orphans",
            ],
            cwd=work_dir,
            timeout=900,
            on_line=on_line,
        )

    def compose_down(self, project: str, compose_file: Path, work_dir: Path) -> CommandResult:
        return self._run(
            [
                "compose",
                "-p",
                project,
                "-f",
                str(compose_file),
                "down",
                "--remove-orphans",
            ],
            cwd=work_dir,
        )

    def compose_ps(self, project: str, compose_file: Path, work_dir: Path) -> CommandResult:
        return self._run(
            [
                "compose",
                "-p",
                project,
                "-f",
                str(compose_file),
                "ps",
                "--format",
                "json",
            ],
            cwd=work_dir,
            timeout=60,
        )

    def compose_restart(
        self, project: str, compose_file: Path, work_dir: Path, services: list[str] | None = None
    ) -> CommandResult:
        args = ["compose", "-p", project, "-f", str(compose_file), "restart"]
        if services:
            args.extend(services)
        return self._run(args, cwd=work_dir)

    def available(self) -> CommandResult:
        return self._run(["version"], timeout=30)

    @staticmethod
    def ensure_clean_dir(path: Path) -> Path:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return path


compose_engine = ComposeEngine()
