from telemetry_agent.pipeline.stats import PipelineStats


def test_pipeline_stats_expose_prometheus_metric_names() -> None:
    stats = PipelineStats(
        line_queue_depth=10,
        line_queue_capacity=2048,
        event_queue_depth=3,
        event_queue_capacity=256,
        lines_dropped=2,
        events_dropped=1,
    )

    metrics = stats.as_metrics()
    assert metrics == {
        "pipeline_line_queue_depth": 10,
        "pipeline_event_queue_depth": 3,
        "pipeline_lines_dropped_total": 2,
        "pipeline_events_dropped_total": 1,
    }
