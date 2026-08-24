class MetricSnapshot(BaseModel):
    instance_id: str
    window_seconds: int
    order_count: int
    rejection_count: int
    execution_count: int
    reject_rate: float