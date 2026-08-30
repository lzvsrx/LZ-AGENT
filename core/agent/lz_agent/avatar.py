from __future__ import annotations

import threading
from enum import StrEnum


class AvatarState(StrEnum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ACTING = "ACTING"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"
    PRIVATE = "PRIVATE"


class AvatarController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = AvatarState.IDLE
        self._reduced_motion = False
        self._enabled = True
        self._sequence = 0

    def update(
        self,
        state: AvatarState,
        *,
        reduced_motion: bool | None = None,
        enabled: bool | None = None,
    ) -> dict:
        with self._lock:
            self._state = state
            if reduced_motion is not None:
                self._reduced_motion = reduced_motion
            if enabled is not None:
                self._enabled = enabled
            self._sequence += 1
            return self._snapshot()

    def current(self) -> dict:
        with self._lock:
            return self._snapshot()

    def _snapshot(self) -> dict:
        animation = "Static" if self._reduced_motion else _ANIMATIONS[self._state]
        return {
            "state": self._state.value,
            "animation": animation,
            "expression": self._state.value.title().replace("_", " "),
            "icon": _ICONS[self._state],
            "reduced_motion": self._reduced_motion,
            "enabled": self._enabled,
            "fallback": "2d-static" if not self._enabled else None,
            "sequence": self._sequence,
        }


_ANIMATIONS = {
    AvatarState.IDLE: "Idle_1",
    AvatarState.LISTENING: "Listening",
    AvatarState.THINKING: "Thinking",
    AvatarState.SPEAKING: "Speaking",
    AvatarState.ACTING: "Acting",
    AvatarState.NEEDS_APPROVAL: "Needs_Approval",
    AvatarState.SUCCESS: "Success",
    AvatarState.WARNING: "Warning",
    AvatarState.ERROR: "Error",
    AvatarState.OFFLINE: "Offline",
    AvatarState.PRIVATE: "Private",
}

_ICONS = {
    AvatarState.IDLE: "circle",
    AvatarState.LISTENING: "microphone",
    AvatarState.THINKING: "progress",
    AvatarState.SPEAKING: "captions",
    AvatarState.ACTING: "tools",
    AvatarState.NEEDS_APPROVAL: "question",
    AvatarState.SUCCESS: "check",
    AvatarState.WARNING: "warning",
    AvatarState.ERROR: "error",
    AvatarState.OFFLINE: "offline",
    AvatarState.PRIVATE: "lock",
}
