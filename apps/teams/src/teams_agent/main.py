"""Entrypoint: `uv run telemetry-teams` serves `POST /api/messages` for Teams."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import httpx
from aiohttp import web
from dotenv import load_dotenv
from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import (
    CloudAdapter,
    jwt_authorization_middleware,
    start_agent_process,
)
from microsoft_agents.hosting.core import (
    AgentApplication,
    Authorization,
    MemoryStorage,
    TurnState,
)

from teams_agent.backend_client import NlBackendClient
from teams_agent.bot import register_handlers
from teams_agent.config import TeamsBotConfig


@web.middleware
async def _authorize(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
) -> web.StreamResponse:
    """Teams JWT validation on every route except the liveness probe."""
    if request.path == "/healthz":
        return await handler(request)
    return await jwt_authorization_middleware(request, handler)  # type: ignore[no-any-return]


def create_app(config: TeamsBotConfig, sdk_config: dict[str, Any]) -> web.Application:
    storage = MemoryStorage()
    connections = MsalConnectionManager(**sdk_config)
    adapter = CloudAdapter(connection_manager=connections)
    agent_app = AgentApplication[TurnState](
        storage=storage,
        adapter=adapter,
        authorization=Authorization(storage, connections, **sdk_config),
        **sdk_config,
    )

    http = httpx.AsyncClient(
        base_url=config.backend_base_url, timeout=config.request_timeout_seconds
    )
    register_handlers(agent_app, NlBackendClient(http), config)

    async def close_backend_client(_app: web.Application) -> AsyncIterator[None]:
        yield
        await http.aclose()

    async def messages(request: web.Request) -> web.Response:
        response = await start_agent_process(request, agent_app, adapter)
        return response if response is not None else web.Response(status=202)

    async def healthz(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    web_app = web.Application(middlewares=[_authorize])
    web_app.router.add_post("/api/messages", messages)
    web_app.router.add_get("/healthz", healthz)
    web_app["agent_configuration"] = connections.get_default_connection_configuration()
    web_app.cleanup_ctx.append(close_backend_client)
    return web_app


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    config = TeamsBotConfig.from_env()
    sdk_config = load_configuration_from_env(os.environ)
    web.run_app(create_app(config, sdk_config), host=config.bind_host, port=config.port)


if __name__ == "__main__":
    main()
