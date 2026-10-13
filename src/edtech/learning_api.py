from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .course_delivery import LearnerProgress, decide_course_access, educator_report
from .phone_identity import InfraiError, InfraiPhoneIdentity


class LearningHandler(BaseHTTPRequestHandler):
    gateway: InfraiPhoneIdentity
    progress = [
        LearnerProgress("learner-14", "Algebra foundations", date(2026, 10, 3), 4, 8),
        LearnerProgress("learner-27", "Algebra foundations", date(2026, 9, 10), 2, 8),
    ]

    def do_POST(self) -> None:
        payload = self._json_body()
        try:
            if self.path == "/signup/code":
                result = self.gateway.start_signup(str(payload["phone"]))
                self._respond(HTTPStatus.ACCEPTED, {"delivery": result})
            elif self.path == "/login/verify":
                result = self.gateway.verify_login(str(payload["phone"]), str(payload["code"]))
                self._respond(HTTPStatus.OK, {"session": result})
            elif self.path == "/deadline/reminder":
                result = self.gateway.send_deadline_reminder(str(payload["phone"]))
                self._respond(HTTPStatus.ACCEPTED, {"reminder": result})
            else:
                self._respond(HTTPStatus.NOT_FOUND, {"error": "route not found"})
        except (KeyError, ValueError) as error:
            self._respond(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except InfraiError as error:
            status = error.status_code if 400 <= error.status_code < 500 else HTTPStatus.BAD_REQUEST
            self._respond(status, {"error": error.code})

    def do_GET(self) -> None:
        if self.path == "/course/access":
            decision = decide_course_access(self.progress[0], date.today())
            self._respond(HTTPStatus.OK, asdict(decision))
        elif self.path == "/educator/report":
            self._respond(HTTPStatus.OK, educator_report(self.progress, date.today()))
        else:
            self._respond(HTTPStatus.NOT_FOUND, {"error": "route not found"})

    def _json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _respond(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve() -> None:
    LearningHandler.gateway = InfraiPhoneIdentity.from_environment()
    server = HTTPServer(("127.0.0.1", 8000), LearningHandler)
    print("Learning API listening on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    serve()
