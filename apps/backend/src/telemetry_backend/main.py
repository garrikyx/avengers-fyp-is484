"""Telemetry Backend entrypoint: serve the public and internal apps.

    uv run telemetry-backend --config config/backend.yaml
    uv run telemetry-backend --check-config

Two uvicorn servers, one process, one `AppDeps` (FR-HLT-012).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

import uvicorn

from telemetry_backend.app import create_internal_app, create_public_app
from telemetry_backend.config import BackendConfigError, load_backend_health_config
from telemetry_backend.deps import AppDeps

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magic Telemetry Backend")
    parser.add_argument("--config", type=Path, default=Path("config/backend.yaml"))
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="validate the config file and exit (spec 011 install runbook)",
    )
    parser.add_argument("--log-level", default="info")
    return parser


async def _serve(deps: AppDeps, log_level: str) -> None:
    public_host, public_port = deps.config.listen_host_port
    internal_host, internal_port = deps.config.internal_listen_host_port
    servers = [
        uvicorn.Server(
            uvicorn.Config(
                create_public_app(deps),
                host=public_host,
                port=public_port,
                log_level=log_level,
            )
        ),
        uvicorn.Server(
            uvicorn.Config(
                create_internal_app(deps),
                host=internal_host,
                port=internal_port,
                log_level=log_level,
            )
        ),
    ]
    logger.info(
        "public API on http://%s:%d, internal probes on http://%s:%d",
        public_host,
        public_port,
        internal_host,
        internal_port,
    )
    await asyncio.gather(*(s.serve() for s in servers))


def main() -> None:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=args.log_level.upper(), format="%(levelname)s %(name)s %(message)s"
    )
    try:
        config = load_backend_health_config(args.config)
    except BackendConfigError as exc:
        raise SystemExit(f"config error: {exc}") from exc
    if args.check_config:
        print(f"config ok: {config}")
        return
    try:
        asyncio.run(_serve(AppDeps(config=config), args.log_level))
    except KeyboardInterrupt:
        # Two uvicorn servers each capture SIGINT and re-raise it on exit; the
        # last re-raise reaches asyncio.run. Same handling as uvicorn.run().
        logger.info("shutdown complete")


if __name__ == "__main__":
    main()
