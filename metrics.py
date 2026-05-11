from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Response

# Define metrics
LOGS_PROCESSED = Counter('logs_processed_total', 'Total number of logs processed', ['level', 'source'])
ANOMALIES_DETECTED = Counter('anomalies_detected_total', 'Total number of anomalies detected')
ANALYSIS_LATENCY = Histogram('analysis_latency_seconds', 'Time spent on AI analysis')

class MetricsManager:
    @staticmethod
    def track_log(level, source):
        LOGS_PROCESSED.labels(level=level, source=source).inc()

    @staticmethod
    def track_anomaly():
        ANOMALIES_DETECTED.inc()

    @staticmethod
    def get_metrics_route():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
