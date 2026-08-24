class TelemetryEvent(BaseModel):
    agent_id: str
    instance_id: str
    event_type: str
    timestamp: datetime