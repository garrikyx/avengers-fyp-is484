"""HTTP routers, one file per concern (spec 007).

`health.py` (UBS-69) serves the agent-liveness read side. Routers never
import each other; `telemetry_backend.main.create_app` composes them.
"""
