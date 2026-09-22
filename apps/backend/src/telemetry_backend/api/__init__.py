"""HTTP routers, one file per concern (spec 007).

`health.py` (UBS-69), `internal.py` (UBS-96), `ingest_placeholder.py`
(temporary, UBS-66 replaces it). Routers never import each other; `app.py`
composes them.
"""
