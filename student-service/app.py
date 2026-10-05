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
