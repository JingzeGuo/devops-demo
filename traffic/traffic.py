import random
import time
from collections import Counter, defaultdict

import requests

URL = "http://localhost:5002/request"

# Same workload distribution for every experiment
workload = ["normal"] * 100 + ["slow"] * 10 + ["error"] * 10

# Keep the request order reproducible
random.seed(42)
random.shuffle(workload)

counts = Counter()
latencies = defaultdict(list)
failed_requests = 0

print(f"Sending {len(workload)} requests...\n")

for i, mode in enumerate(workload, start=1):
    start = time.perf_counter()

    try:
        response = requests.get(
            URL,
            params={"mode": mode},
            timeout=5,
        )

        elapsed = time.perf_counter() - start

        counts[mode] += 1
        latencies[mode].append(elapsed)

    except requests.RequestException as e:
        failed_requests += 1
        print(f"Request {i} failed: {e}")

    if i % 20 == 0:
        print(f"Sent {i}/{len(workload)} requests")

print("\n=== Traffic Summary ===")

for mode in ["normal", "slow", "error"]:
    avg_latency = sum(latencies[mode]) / len(latencies[mode])

    print(f"{mode:6} | sent: {counts[mode]:3} | avg latency: {avg_latency:.2f}s")

print(f"\nFailed requests: {failed_requests}")
