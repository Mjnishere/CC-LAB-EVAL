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
