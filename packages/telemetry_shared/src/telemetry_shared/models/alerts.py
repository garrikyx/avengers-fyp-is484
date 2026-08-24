class AlertEvent(BaseModel):
    alert_id: str
    instance_id: str
    rule_name: str
    severity: str
    observed_value: float
    threshold: float
    timestamp: datetime