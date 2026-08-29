from __future__ import annotations

import os
import platform
import uuid
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    session_device_id: str
    device_type: str
    operating_system: str
    os_version: str
    architecture: str
    processor: str
    logical_cpus: int
    device_name: str | None
    privacy_notice: str


class DeviceDetector:
    def __init__(self) -> None:
        self.session_device_id = str(uuid.uuid4())

    def profile(self, include_name: bool = False) -> dict:
        system = platform.system() or "Unknown"
        profile = DeviceProfile(
            session_device_id=self.session_device_id,
            device_type=self._device_type(system),
            operating_system=system,
            os_version=platform.version() or platform.release(),
            architecture=platform.machine() or "unknown",
            processor=platform.processor() or "unknown",
            logical_cpus=os.cpu_count() or 1,
            device_name=platform.node() if include_name else None,
            privacy_notice=(
                "O nome do dispositivo só é incluído quando solicitado; "
                "o identificador muda ao reiniciar o núcleo."
            ),
        )
        return asdict(profile)

    @staticmethod
    def _device_type(system: str) -> str:
        if system == "Android" or "ANDROID_ROOT" in os.environ:
            return "mobile-or-tablet"
        if system in {"Windows", "Linux", "Darwin"}:
            return "desktop-or-laptop"
        return "unknown"
