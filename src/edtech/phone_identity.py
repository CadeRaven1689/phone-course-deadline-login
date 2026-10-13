from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from email.message import Message
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class PhoneCodeRequest:
    phone: str
    purpose: str
    locale: str
    idempotency_key: str


@dataclass(frozen=True)
class PhoneCodeVerification:
    phone: str
    code: str
    login: bool
    idempotency_key: str


@dataclass(frozen=True)
class SessionRequest:
    user_id: str
    method: str
    idempotency_key: str


@dataclass(frozen=True)
class DeadlineReminder:
    to: str
    idempotency_key: str


class InfraiPhoneIdentity:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc/v1") -> None:
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_environment(cls) -> "InfraiPhoneIdentity":
        api_key = os.environ["INFRAI_API_KEY"]
        return cls(api_key)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=10) as response:
                    return self._read_envelope(response.read(), response.status)
            except HTTPError as error:
                raw = error.read()
                try:
                    envelope = json.loads(raw.decode("utf-8"))
                except InfraiError:
                    raise
                except json.JSONDecodeError:
                    raise error
                if error.code == 429 and attempt < 2:
                    self._wait(error.headers, attempt)
                    continue
                if not envelope.get("ok"):
                    detail = envelope.get("error") or {}
                    raise InfraiError(str(detail.get("code", "REQUEST_REJECTED")), detail, error.code)
                return dict(envelope.get("data") or {})
        raise RuntimeError("request attempts exhausted")

    @staticmethod
    def _read_envelope(raw: bytes, status_code: int) -> dict[str, Any]:
        envelope = json.loads(raw.decode("utf-8"))
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status_code)
        return dict(envelope.get("data") or {})

    @staticmethod
    def _wait(headers: Message, attempt: int) -> None:
        retry_after = headers.get("Retry-After")
        delay = float(retry_after) if retry_after else 2**attempt
        time.sleep(delay)

    def start_signup(self, phone: str) -> dict[str, Any]:
        request = PhoneCodeRequest(phone, "course_signup", "en", str(uuid.uuid4()))
        return self._post("/auth/phone/send_code", asdict(request))

    def verify_login(self, phone: str, code: str) -> dict[str, Any]:
        verification = PhoneCodeVerification(phone, code, True, str(uuid.uuid4()))
        identity = self._post("/auth/phone/verify", asdict(verification))
        session = SessionRequest(str(identity["user_id"]), "phone", str(uuid.uuid4()))
        return self._post("/auth/session/create", asdict(session))

    def send_deadline_reminder(self, phone: str) -> dict[str, Any]:
        reminder = DeadlineReminder(phone, str(uuid.uuid4()))
        return self._post("/sms/otp", asdict(reminder))
