from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "product_reco_bot.management.app:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )
