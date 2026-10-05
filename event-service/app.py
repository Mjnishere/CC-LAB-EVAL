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
