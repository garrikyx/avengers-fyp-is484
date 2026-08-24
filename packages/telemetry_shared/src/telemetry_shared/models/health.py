class AgentHeartbeat(BaseModel):
    agent_id: str
    instance_id: str
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    queue_depth: int