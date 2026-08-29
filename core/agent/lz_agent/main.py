import os

import uvicorn

from .api import create_app

app = create_app()


def run() -> None:
    uvicorn.run(
        "lz_agent.main:app",
        host=os.getenv("LZ_AGENT_HOST", "127.0.0.1"),
        port=int(os.getenv("LZ_AGENT_PORT", "8765")),
        reload=False,
    )


if __name__ == "__main__":
    run()
