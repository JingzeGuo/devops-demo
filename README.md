# OpenTelemetry Tail Sampling Demo

A small DevOps demo showing how trace sampling policies affect the observability of failures and slow requests in a distributed system.

The demo uses two HTTP services instrumented with OpenTelemetry, an OpenTelemetry Collector, and Jaeger for trace visualization.

The main goal is to compare:

1. **Uniform probabilistic sampling** — retain approximately 10% of all traces.
2. **Tail-aware sampling** — retain all error and slow traces while still sampling approximately 10% of normal traces.

## Architecture

```text
Client / Traffic Generator
          |
          v
    +-----------+
    | service-a |
    +-----+-----+
          |
          | HTTP
          v
    +-----------+
    | service-b |
    +-----------+
          |
          | OpenTelemetry spans
          v
+------------------------+
| OpenTelemetry Collector|
+-----------+------------+
            |
            | OTLP
            v
       +---------+
       | Jaeger  |
       +---------+
```

`service-a` receives the external request and calls `service-b`.

OpenTelemetry propagates the trace context between the two services so that their spans belong to the same distributed trace.

A typical trace therefore looks like:

```text
service-a: GET /request
└── service-a: HTTP request to service-b
    └── service-b: GET /work
```

## Components

### service-a

The entry point of the demo application.

It exposes:

```text
GET /request?mode=<mode>
```

and forwards the request to `service-b`.

### service-b

Simulates three types of application behaviour:

| Mode | Behaviour |
|---|---|
| `normal` | Returns successfully with low latency |
| `slow` | Delays the response before returning successfully |
| `error` | Returns HTTP 500 |

### OpenTelemetry

Both Python services use OpenTelemetry auto-instrumentation.

It automatically creates spans for:

- incoming Flask requests
- outgoing HTTP requests
- distributed trace-context propagation between the services

### OpenTelemetry Collector

The Collector receives traces from both services through OTLP.

The sampling policy is configured in `collector.yaml`.

During the demo, only the Collector configuration will be changed. The application services and workload remain unchanged.

### Jaeger

Jaeger stores and visualizes the traces retained by the Collector.

The UI is available at:

```text
http://localhost:16686
```

### Traffic generator

`traffic/traffic.py` will generate a repeatable workload containing:

- normal requests
- slow requests
- failed requests

The same workload is used before and after changing the sampling policy so that the two configurations can be compared fairly.

## Project Structure

```text
devops-demo/
├── docker-compose.yml
├── collector.yaml
├── README.md
├── service-a/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── service-b/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
└── traffic/
    └── traffic.py
```

## Running the Demo

Build and start the services:

```bash
docker compose up --build
```

The services are then available at:

```text
service-a: http://localhost:5002
Jaeger UI: http://localhost:16686
```

`service-b` is not exposed to the host because it is only accessed internally by `service-a` through the Docker Compose network.

## Manual Testing

Normal request:

```bash
curl "http://localhost:5002/request?mode=normal"
```

Slow request:

```bash
curl "http://localhost:5002/request?mode=slow"
```

Error request:

```bash
curl "http://localhost:5002/request?mode=error"
```

After sending requests, open Jaeger:

```text
http://localhost:16686
```

Select `service-a` and inspect the resulting traces.

A single trace should contain spans from both `service-a` and `service-b`, demonstrating distributed context propagation.

## Sampling Experiment

The demo compares two sampling configurations.

### Round 1 — Uniform sampling

The Collector retains approximately 10% of all traces regardless of their outcome.

Conceptually:

```text
normal → ~10%
slow   → ~10%
error  → ~10%
```

This reduces the amount of trace data stored in Jaeger, but rare failures or slow requests may also be discarded.

### Round 2 — Tail-aware sampling

The Collector configuration is changed so that:

```text
error traces → 100%
slow traces  → 100%
normal traces → ~10%
```

Only the Collector is restarted:

```bash
docker compose restart otel-collector
```

The same workload is then generated again.

This allows us to compare how much diagnostically useful information is retained under the two policies.

## Why Tail Sampling?

With head sampling, the sampling decision is normally made when a trace begins.

At that point, the system does not yet know whether the request will:

- fail
- become unusually slow
- complete normally

Tail sampling delays the decision until more of the trace has been collected.

Conceptually:

```text
receive spans
     |
     v
group by trace ID
     |
     v
buffer trace
     |
     v
evaluate completed trace
     |
     +--> keep
     |
     └--> drop
```

This makes it possible to preferentially retain traces that contain errors or exceed a latency threshold.

## Trade-offs

Tail sampling provides more informed sampling decisions, but it also introduces additional costs.

### Memory

The Collector must temporarily buffer trace data before making a sampling decision.

### Decision delay

Traces cannot be exported immediately because the Collector has to wait for enough spans to arrive.

### Scaling

In a deployment with multiple Collectors, all spans belonging to the same trace must reach the same tail-sampling Collector.

Otherwise, no single Collector may have enough information to correctly evaluate the entire trace.

### Network traffic

Tail sampling reduces the number of traces exported to the backend such as Jaeger.

However, it does **not** reduce the telemetry traffic sent from the application services to the Collector, because the Collector must first receive the spans before making the sampling decision.
