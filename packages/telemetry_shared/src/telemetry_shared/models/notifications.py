"""Alert notification sent from the backend to the Teams app (UBS-120).

The backend posts one of these to the Teams app's `POST /api/notify` for each
firing or resolved transition, and the Teams app renders it as an Adaptive
Card in the configured group chat. The alert itself is the same `AlertRecord`
`GET /telemetry/alerts` returns, so the card never shows anything the alert
API would not.
"""

from __future__ import annotations

from typing import Literal

from telemetry_shared.models._base import CamelModel
from telemetry_shared.models.alerts_query import AlertRecord

NotificationKind = Literal["firing", "resolved"]


class AlertNotification(CamelModel):
    schema_version: Literal[1] = 1
    kind: NotificationKind
    alert: AlertRecord

    @property
    def dedupe_key(self) -> str:
        """`alertId:kind`: each occurrence posts at most one card per kind."""
        return f"{self.alert.alert_id}:{self.kind}"
