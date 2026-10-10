"""
system_info.py - Read-only system information tools for VERONICA.
"""

import os
import platform
import shutil

try:
    import psutil
except ImportError:
    psutil = None

from tools.base import BaseTool


class SystemInfoTool(BaseTool):
    name = "get_system_info"
    description = (
        "Gets read-only information about the user's computer, including "
        "operating system, CPU usage, RAM usage, and disk usage."
    )

    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self, **kwargs) -> str:
        try:
            system = platform.system()
            release = platform.release()
            machine = platform.machine()

            lines = [
                f"Operating system: {system} {release}",
                f"Architecture: {machine}",
                f"CPU cores: {os.cpu_count() or 'Unknown'}",
            ]

            if psutil:
                cpu = psutil.cpu_percent(interval=0.5)
                memory = psutil.virtual_memory()

                total_ram_gb = memory.total / (1024 ** 3)
                used_ram_gb = memory.used / (1024 ** 3)

                disk = shutil.disk_usage(os.getcwd())
                total_disk_gb = disk.total / (1024 ** 3)
                free_disk_gb = disk.free / (1024 ** 3)

                lines.extend([
                    f"CPU usage: {cpu:.1f}%",
                    f"RAM usage: {memory.percent:.1f}% "
                    f"({used_ram_gb:.1f} GB / {total_ram_gb:.1f} GB)",
                    f"Disk free: {free_disk_gb:.1f} GB "
                    f"of {total_disk_gb:.1f} GB",
                ])

            return "\n".join(lines)

        except Exception as e:
            return f"Unable to retrieve system information: {e}"