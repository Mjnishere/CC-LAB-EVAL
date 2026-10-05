# Microservice Lab — Implementation Plan

## Overview

**Domain chosen:** College Fest Management — **"Festify"**

**Concept:** Students register for events at a college fest. When a student registers, the system:
1. Validates the student details (Student Service)
2. Checks if the event has available slots (Event Service)
3. Books the registration and issues a confirmation (Registration Service)

**Architecture:**
```
Client → Registration Service → Student Service
                              → Event Service
```

Three independent microservices, each with their own REST API, all containerized with Docker and wired together via Docker Compose.

**Tech stack (keep it simple):**
- Language: **Python** (Flask) — minimal boilerplate, fast to demo
- Containerization: **Docker + Docker Compose**
- Load testing: **k6** — modern load testing tool, clean JS scripts, great output
- Graphs: **Python** (matplotlib + pandas) — script generates all 4 graphs automatically

---

## Project Folder Structure

```
cc/
├── student-service/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── event-service/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── registration-service/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── load_test.js          ← k6 load test script
├── run_tests.sh          ← shell script that runs all 5 levels and saves CSVs
├── plot_graphs.py        ← Python script that reads results and plots 4 graphs
└── results/
    ├── w1.csv ... w5.csv ← k6 output per level
    └── observations.md   ← fill this in after testing
```


---

## Checkpoint 1 — Design and Develop the Microservices

### Service Responsibilities

| Service | Port | Responsibility |
|---|---|---|
| **Student Service** | 5001 | Stores student info — returns student details by ID |
| **Event Service** | 5002 | Stores fest events — returns event details and checks seat availability |
| **Registration Service** | 5003 | Registers a student for an event — calls Student & Event services internally |

### student-service/app.py
```python
from flask import Flask, jsonify
app = Flask(__name__)

STUDENTS = {
    "S01": {"id": "S01", "name": "Arjun Sharma",  "branch": "CSE", "year": 3},
    "S02": {"id": "S02", "name": "Priya Nair",    "branch": "ECE", "year": 2},
    "S03": {"id": "S03", "name": "Rahul Mehta",   "branch": "ME",  "year": 4},
}

@app.route("/students/<student_id>")
def get_student(student_id):
    student = STUDENTS.get(student_id)
    if student:
        return jsonify(student)
    return jsonify({"error": "Student not found"}), 404

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "student-service"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
```

### event-service/app.py
```python
from flask import Flask, jsonify
app = Flask(__name__)

EVENTS = {
    "E01": {"id": "E01", "name": "Hackathon",       "venue": "Lab Block",   "seats_available": 50},
    "E02": {"id": "E02", "name": "Battle of Bands",  "venue": "Open Air",   "seats_available": 200},
    "E03": {"id": "E03", "name": "Code Sprint",      "venue": "Seminar Hall","seats_available": 30},
}

@app.route("/events/<event_id>")
def get_event(event_id):
    event = EVENTS.get(event_id)
    if event:
        return jsonify(event)
    return jsonify({"error": "Event not found"}), 404

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "event-service"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
```

### registration-service/app.py
```python
import os, requests
from flask import Flask, jsonify, request
app = Flask(__name__)

STUDENT_URL = os.getenv("STUDENT_SERVICE_URL", "http://student-service:5001")
EVENT_URL   = os.getenv("EVENT_SERVICE_URL",   "http://event-service:5002")

@app.route("/register", methods=["POST"])
def register():
    data       = request.get_json(force=True)
    student_id = data.get("student_id", "S01")
    event_id   = data.get("event_id",   "E01")

    # Call Student Service
    student_resp = requests.get(f"{STUDENT_URL}/students/{student_id}", timeout=5)
    if student_resp.status_code != 200:
        return jsonify({"error": "Student not found"}), 404
    student = student_resp.json()

    # Call Event Service
    event_resp = requests.get(f"{EVENT_URL}/events/{event_id}", timeout=5)
    if event_resp.status_code != 200:
        return jsonify({"error": "Event not found"}), 404
    event = event_resp.json()

    # Check seat availability
    if event["seats_available"] < 1:
        return jsonify({"error": "No seats available"}), 409

    return jsonify({
        "registration_id": f"REG-{student_id}-{event_id}",
        "student":         student,
        "event":           event,
        "status":          "confirmed",
        "message":         f"{student['name']} successfully registered for {event['name']}!"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "registration-service"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
```

### requirements.txt (same for all three services)
```
flask==3.0.3
requests==2.32.3
```

### How to test locally (before Docker)
```bash
# Terminal 1
cd student-service && pip install -r requirements.txt && python app.py

# Terminal 2
cd event-service && pip install -r requirements.txt && python app.py

# Terminal 3 (point to localhost for local test)
STUDENT_SERVICE_URL=http://localhost:5001 \
EVENT_SERVICE_URL=http://localhost:5002 \
python registration-service/app.py

# Terminal 4 — quick sanity checks
curl http://localhost:5001/students/S01
curl http://localhost:5002/events/E01
curl -X POST http://localhost:5003/register \
     -H "Content-Type: application/json" \
     -d '{"student_id":"S01","event_id":"E01"}'
```

**Checkpoint 1 done** when all three services return expected JSON independently.

---

## Checkpoint 2 — Containerize and Deploy

### Dockerfile (identical for all three — just copy it into each folder)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
CMD ["python", "app.py"]
```

### docker-compose.yml
```yaml
version: "3.9"

services:
  student-service:
    build: ./student-service
    ports:
      - "5001:5001"
    networks:
      - fest-network

  event-service:
    build: ./event-service
    ports:
      - "5002:5002"
    networks:
      - fest-network

  registration-service:
    build: ./registration-service
    ports:
      - "5003:5003"
    environment:
      - STUDENT_SERVICE_URL=http://student-service:5001
      - EVENT_SERVICE_URL=http://event-service:5002
    depends_on:
      - student-service
      - event-service
    networks:
      - fest-network

networks:
  fest-network:
    driver: bridge
```

### Build & deploy commands
```bash
# Build all images
docker compose build

# Verify images exist
docker images

# Start all containers
docker compose up -d

# Verify all 3 are running
docker compose ps
```

**Checkpoint 2 done** when `docker compose ps` shows all three containers with status `Up`.

---

## Checkpoint 3 — Inter-Service Communication

Docker Compose automatically places all services on `fest-network`. The Registration Service reaches the other two using their **service names as hostnames** (`http://student-service:5001`, `http://event-service:5002`). Docker's internal DNS resolves these names — no IPs are hardcoded anywhere.

### Demo the end-to-end flow
```bash
# A student registers for a fest event — touches all 3 services
curl -X POST http://localhost:5003/register \
     -H "Content-Type: application/json" \
     -d '{"student_id":"S02","event_id":"E02"}'
```

Expected response:
```json
{
  "registration_id": "REG-S02-E02",
  "student": {"id": "S02", "name": "Priya Nair", "branch": "ECE", "year": 2},
  "event":   {"id": "E02", "name": "Battle of Bands", "venue": "Open Air", "seats_available": 200},
  "status":  "confirmed",
  "message": "Priya Nair successfully registered for Battle of Bands!"
}
```

**To the evaluator:** *"When the client POSTs to the Registration Service, it makes two internal HTTP calls — one to Student Service to validate the student, and one to Event Service to check seat availability. Both calls use Docker Compose service names as hostnames. Docker's internal DNS on the `fest-network` bridge resolves them to the correct container IPs. The final confirmation is assembled and returned to the client — a true microservice orchestration flow."*

**Checkpoint 3 done** when the above response is live.

---

## Checkpoint 4 — Load Testing and Monitoring

### Install k6
```bash
brew install k6
```

### load_test.js — single k6 script (concurrency passed via env var)
```javascript
import http from "k6/http";
import { check, sleep } from "k6";

const VUS = parseInt(__ENV.VUS) || 1;   // concurrent virtual users

export const options = {
  vus:      VUS,
  duration: "15s",
};

const PAYLOAD = JSON.stringify({ student_id: "S01", event_id: "E01" });
const HEADERS  = { "Content-Type": "application/json" };

export default function () {
  const res = http.post("http://localhost:5003/register", PAYLOAD, { headers: HEADERS });
  check(res, { "status is 200": (r) => r.status === 200 });
  sleep(0.1);
}
```

### run_tests.sh — runs all 5 levels and saves CSV output
```bash
#!/bin/bash
# Run from project root after containers are up

mkdir -p results

LEVELS=(1 2 4 8 16)

echo "==============================="
echo "  Festify k6 Load Tests"
echo "==============================="

for VUS in "${LEVELS[@]}"; do
    echo ""
    echo "--- VUs (concurrency): $VUS ---"
    k6 run \
      --env VUS=$VUS \
      --out csv=results/w${VUS}.csv \
      --summary-trend-stats="avg,p(95),max" \
      load_test.js
    echo "Results saved to results/w${VUS}.csv"
done
```

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Monitor containers during the test (separate terminal)
```bash
# Watch live CPU and memory for all 3 containers
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

> k6 prints a summary after each level — note **avg response time**, **req/s**, and **failed checks**. Note CPU/memory peaks from `docker stats` at each level.

### What to record per workload level

| Metric | Where to find it |
|---|---|
| **Response time (ms)** | k6 summary → `http_req_duration` avg |
| **Throughput (req/s)** | k6 summary → `http_reqs` rate |
| **Failed requests** | k6 summary → `checks` failed count |
| **CPU %** | `docker stats` — note peak during each level |
| **Memory** | `docker stats` — note peak during each level |

### Sample Observation Table (fill with real values)

| Workload | Concurrency | Resp. Time (ms) | Throughput (req/s) | Failed | CPU % | Memory (MB) |
|---|---|---|---|---|---|---|
| W1 | 1  | ___ | ___ | 0 | ___ | ___ |
| W2 | 2  | ___ | ___ | 0 | ___ | ___ |
| W3 | 4  | ___ | ___ | 0 | ___ | ___ |
| W4 | 8  | ___ | ___ | 0 | ___ | ___ |
| W5 | 16 | ___ | ___ | ___ | ___ | ___ |

**Checkpoint 4 done** when the table is filled with real measured numbers.

---

## Checkpoint 5 — Analysis and Presentation

### Graphs to prepare (4 required)

Use **Python + matplotlib** to generate all 4 graphs automatically from your observation data.

#### Install dependencies
```bash
pip install matplotlib pandas
```

#### plot_graphs.py
```python
import pandas as pd
import matplotlib.pyplot as plt
import os

# ─── Paste your real measured values here ───────────────────────────────────
data = {
    "concurrency":    [1,   2,   4,   8,   16],
    "response_time":  [0,   0,   0,   0,   0],   # ms  — fill from k6 output
    "throughput":     [0,   0,   0,   0,   0],   # req/s
    "cpu":            [0,   0,   0,   0,   0],   # %   — from docker stats
    "memory":         [0,   0,   0,   0,   0],   # MB
}
# ────────────────────────────────────────────────────────────────────────────

df = pd.DataFrame(data)
os.makedirs("results", exist_ok=True)

graphs = [
    ("response_time", "Avg Response Time (ms)", "Response Time vs Concurrency",   "response_time.png"),
    ("throughput",    "Throughput (req/s)",      "Throughput vs Concurrency",       "throughput.png"),
    ("cpu",           "CPU Utilization (%)",     "CPU Utilization vs Concurrency",  "cpu.png"),
    ("memory",        "Memory Usage (MB)",       "Memory Usage vs Concurrency",     "memory.png"),
]

for col, ylabel, title, filename in graphs:
    plt.figure(figsize=(7, 4))
    plt.plot(df["concurrency"], df[col], marker="o", linewidth=2, color="steelblue")
    plt.title(title, fontsize=14)
    plt.xlabel("Concurrent Requests (VUs)")
    plt.ylabel(ylabel)
    plt.xticks(df["concurrency"])
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"results/{filename}", dpi=150)
    plt.close()
    print(f"Saved results/{filename}")

print("\nAll 4 graphs saved to results/")
```

#### Run it
```bash
python plot_graphs.py
```

Graphs are saved to `results/` as PNG files — ready to include in your report or show on screen during demo.

### Talking points for the evaluator

1. **Architecture** — Festify has 3 microservices: Student Service manages student data, Event Service manages fest events, and Registration Service orchestrates both to complete a registration. Each service is independently deployable and has a single clear responsibility.

2. **Containerization** — Every service has its own Dockerfile using a slim Python 3.12 base. Images are built via `docker compose build` and run via `docker compose up -d`. Each service runs in its own isolated container.

3. **Communication** — All three containers share a Docker bridge network called `fest-network`. Registration Service calls Student and Event services using their Compose service names as hostnames (`http://student-service:5001`). Docker's internal DNS resolves these — no hardcoded IPs anywhere.

4. **Load Testing** — Used **k6** to simulate virtual users at 5 concurrency levels: 1, 2, 4, 8, 16. Each level runs for 15 seconds. k6 reports avg response time, throughput (req/s), and failed checks per level. Monitored CPU/memory live with `docker stats`.

5. **Results** — As concurrency increases, response time rises (more requests queuing). Throughput grows initially then plateaus. Registration Service uses the most CPU because each request triggers two outbound HTTP calls to the other services.

6. **Graphs** — Generated all 4 required graphs using a **Python script** (matplotlib + pandas) — response time, throughput, CPU, and memory vs concurrency. Saved as PNG files.

7. **Conclusion** — Registration Service is the bottleneck — it does the most work per request. Under high load, response time degrades. In a real production system, we'd horizontally scale the Registration Service (run multiple replicas behind a load balancer).

---

## Quick Execution Checklist

```
[ ] Create folder structure (student-service, event-service, registration-service)
[ ] Write app.py in each folder
[ ] Write requirements.txt (same content) in each folder
[ ] Write Dockerfile (same content) in each folder
[ ] Write docker-compose.yml at root
[ ] Optional: test services locally with curl
[ ] docker compose build
[ ] docker compose up -d
[ ] docker compose ps           ← verify all 3 running
[ ] curl end-to-end /register   ← verify Checkpoint 3
[ ] brew install k6
[ ] ./run_tests.sh              (watch docker stats in a second terminal)
[ ] Fill in observation table with real numbers from k6 output
[ ] pip install matplotlib pandas
[ ] Fill values into plot_graphs.py → python plot_graphs.py
[ ] 4 PNGs saved to results/    ← show these during demo
[ ] Prepare 5-minute verbal explanation
```

---

## Estimated Time to Complete

| Task | Time |
|---|---|
| Write all 3 Flask apps | 30 min |
| Dockerfiles + docker-compose.yml | 15 min |
| Build, deploy, verify | 15 min |
| Load testing + recording results | 20 min |
| Graphs + observation table | 20 min |
| **Total** | **~100 min** |
