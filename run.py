"""Entry point: start every configured agent in a single asyncio loop."""
from __future__ import annotations

import asyncio
import logging

from bots.designer import DesignerAgent
from bots.developer import DeveloperAgent
from bots.pm import PMAgent
from bots.qa import QAAgent
from core.agent import BaseAgent
from core.memory import Memory
from settings import AGENTS, DB_PATH

logger = logging.getLogger("run")

AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "pm": PMAgent,
    "developer": DeveloperAgent,
    "qa": QAAgent,
    "designer": DesignerAgent,
}


async def main() -> None:
    if not AGENTS:
        logger.error(
            "no agents configured; set at least one *_BOT_TOKEN in .env"
        )
        return

    memory = Memory(DB_PATH)
    tasks = []
    for name, cfg in AGENTS.items():
        cls = AGENT_CLASSES.get(name)
        if cls is None:
            logger.warning("no class registered for agent %s, skipping", name)
            continue
        agent = cls(token=cfg.token, model=cfg.model, memory=memory)
        logger.info("loaded %s with model %s", name, cfg.model)
        tasks.append(agent.start())

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("shutdown requested")
