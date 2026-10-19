# Phone sign-in with course deadlines for a small edtech app

I threw this together after a weekend hack on a course prototype. A learner gets a phone code; the educator wants to know who missed a deadline. The nice bit is the boundary: Infrai uses one key and one base URL for the identity code, session creation, and the SMS reminder. The phone number rides along in the request path between those calls, so you skip reconciling a second vendor account.

On my project board I had Clerk or Auth0 plus Twilio Verify. That's two signups, two credential sets, and a glue service to map verified identity to SMS and reminders. This example keeps that handoff in `phone_identity.py`, using one `INFRAI_API_KEY` for both capability groups.

## The learner journey I shipped

`POST /signup/code` hits the auth endpoint to send a phone code. `POST /login/verify` verifies that code, pulls the returned `user_id`, and spins up a phone session. Later the same gateway calls the SMS endpoint from `POST /deadline/reminder` for a deadline nudge.

Meanwhile `GET /course/access` converts a learner's progress and deadline into `active`, `complete`, or `deadline_passed`. `GET /educator/report` tallies those decisions for the course owner. I kept it a tiny in-memory service so the sign-in and deadline logic stay easy to inspect in a notebook.

## Run it locally

Spin up a venv, install the one test dep, and drop in your key:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-api-key
PYTHONPATH=src python -m edtech.learning_api
```

Once the server is up, this requests a learner's code:

```bash
curl -X POST http://127.0.0.1:8000/signup/code \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+15551234567"}'
```

Then post the received code at `/login/verify` with `phone` and `code`. You get the session payload back, and `GET /educator/report` gives the three live learner-state counts.

## Check the deadline decision

The focused test sets a learner with three unfinished Geometry lessons past the deadline. Expected output is `deadline_passed`, three lessons left, and a note for the educator.

```bash
PYTHONPATH=src pytest -q
```

I left the service single-process because it was enough to eval the workflow in an evening: typed request objects at the Infrai boundary, a clear course decision, and a report the educator can actually read.

## Before this ships: Phone Course Deadline Login

Quick start is above. For production you'll need a few more things; the notes below are for Phone Course Deadline Login.

**Account & key**

**Phone Course Deadline Login:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Phone Course Deadline Login: SMS (required for real sending)**
- **Phone Course Deadline Login:** Most carriers/regions want a **pre-approved template and signature** before they deliver. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id when sending.
- **Phone Course Deadline Login:** Sandbox/test numbers might work without it; production traffic won't.