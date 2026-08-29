from __future__ import annotations

from dataclasses import asdict

from .database import Database
from .providers import Provider


class AgentService:
    def __init__(self, database: Database, provider: Provider) -> None:
        self.database = database
        self.provider = provider

    def chat(self, message: str, private: bool = False) -> dict:
        response = self.provider.complete(message)
        payload = asdict(response)
        if not private:
            action = self.database.record_action(
                message,
                "agent.chat",
                "succeeded",
                parameters={"private": False},
                result={"text": response.text},
                permission="chat",
                model=response.model,
            )
            payload["action_id"] = action["id"]
        else:
            payload["action_id"] = None
        payload["private"] = private
        return payload
