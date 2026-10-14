# Monitoring

## Metrics

The FastAPI process exposes `/metrics` in Prometheus text format. Current application metrics:

- `scoutline_http_requests_total{method,route,status}`
- `scoutline_http_request_duration_seconds{method,route}`

The route label uses FastAPI's route template, not the raw URL, which prevents IDs and query strings from creating unbounded time series. The metrics middleware excludes `/metrics` itself. Prometheus' own process/runtime metrics may also appear through the default registry.

## Dashboard

Grafana provisions the Prometheus data source and the `Scoutline - Service Overview` dashboard from files in `grafana/provisioning` and `grafana/dashboards`. It displays request throughput, 5xx rate, p50/p95/p99 latency, status-code rates, and backend scrape availability.

## Alert rules

Prometheus loads rules from `prometheus/alerts.yml`:

- backend scrape target down for 2 minutes;
- HTTP 5xx rate above 5% for 5 minutes;
- p95 request latency above 1 second for 10 minutes.

Tune thresholds based on real traffic and an agreed service-level objective. These are initial defaults, not validated SLOs.

## Notification limitation

Rules can enter a firing state in Prometheus, but no Alertmanager notification route or receiver is configured here. Do not claim email, Slack, or pager notification works until Alertmanager and a test receiver are configured and verified.

## Access

The production-like Compose file binds Prometheus and Grafana to loopback. Keep them private or place them behind a properly authenticated TLS-protected access layer. Set `GRAFANA_ADMIN_PASSWORD` before enabling monitoring.
