import http from "k6/http";
import { check, sleep } from "k6";

const VUS = parseInt(__ENV.VUS) || 1; // concurrent virtual users

export const options = {
  vus: VUS,
  duration: "15s",
};

const PAYLOAD = JSON.stringify({ student_id: "S01", event_id: "E01" });
const HEADERS = { "Content-Type": "application/json" };

export default function () {
  const res = http.post("http://localhost:5003/register", PAYLOAD, { headers: HEADERS });
  check(res, { "status is 200": (r) => r.status === 200 });
  sleep(0.1);
}
