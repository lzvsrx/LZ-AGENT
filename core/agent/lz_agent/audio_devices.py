from __future__ import annotations

from typing import Any

try:
    import sounddevice
except (ImportError, OSError):  # pragma: no cover - platform fallback
    sounddevice = None


def input_devices() -> dict[str, Any]:
    if sounddevice is None:
        return {
            "available": False,
            "devices": [],
            "default_input": None,
            "reason": "Backend de áudio não disponível; entrada por texto continua ativa.",
        }
    try:
        devices = sounddevice.query_devices()
        default_input = sounddevice.default.device[0]
    except Exception as error:  # PortAudio reports platform-specific errors.
        return {
            "available": False,
            "devices": [],
            "default_input": None,
            "reason": f"Não foi possível consultar os microfones: {error}",
        }
    inputs = [
        {
            "id": index,
            "name": str(device["name"]),
            "channels": int(device["max_input_channels"]),
            "default_sample_rate": int(device["default_samplerate"]),
            "is_default": index == default_input,
        }
        for index, device in enumerate(devices)
        if int(device["max_input_channels"]) > 0
    ]
    return {
        "available": bool(inputs),
        "devices": inputs,
        "default_input": default_input if default_input >= 0 else None,
        "reason": None if inputs else "Nenhum microfone foi detectado.",
    }
