# ShieldID - Privacy-Preserving Identity for Young Users

ShieldID is a Django-based hackathon prototype for pseudonymous identity verification. It lets platforms verify a user and age range without receiving personal information.

## What Is Implemented

- Encrypted identity storage (`name`, `email`, `age`) using Fernet from `cryptography`
- Pseudonymous ID generation in `SH-XXXX-XXXX` format
- Public verification endpoint exposing only `verified`, `age_range`, and pseudonym
- Consent endpoint that releases selected fields only when a passkey challenge assertion is provided
- Certificate model and lookup endpoint tied to pseudonym (not real name)
- Session-scoped user dashboard to re-check generated ShieldIDs without full auth rollout
- Tailwind-powered demo UI:
  - Landing page
  - Registration flow
  - Session dashboard for "my keys"
  - Verification checker
  - Mock EdTech integration + certificate issuance
- Admin integration for reviewing encrypted records

## Tech Stack

- Django 6
- Django REST Framework
- `cryptography` (Fernet)
- `webauthn` (py_webauthn ecosystem package)
- SQLite
- Django templates + Tailwind CDN

## Quick Start (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

Open: `http://localhost:8000`

## Quick Start (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Environment Variables

- `ENCRYPTION_KEY` (optional): Fernet key for PII encryption. If unset, a deterministic demo key is derived from Django `SECRET_KEY`.
- `PASSKEY_RP_ID` (optional, default `localhost`)
- `PASSKEY_RP_NAME` (optional, default `ShieldID Demo`)

To generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## API Endpoints

- `POST /api/register/`
  - body: `{ "name": "...", "age": 15, "email": "..." }`
  - returns: `shield_id`, `age_range`, passkey challenge/options, and a demo certificate ID
- `GET /api/verify/<shield_id>/`
  - returns only safe verification metadata
- `GET /api/me/keys/`
  - returns session-bound list of ShieldIDs generated/attached from the same browser session
- `POST /api/me/keys/add/`
  - body: `{ "shield_id": "SH-XXXX-XXXX" }`
  - attaches an existing ID to the current session dashboard
- `POST /api/me/keys/clear/`
  - clears session dashboard entries
- `POST /api/consent/<shield_id>/`
  - body: `{ "passkey_assertion": "...", "fields": ["name", "age"] }`
  - returns selected fields when assertion matches current challenge
- `GET /api/certificate/<shield_id>/<cert_id>/`
  - returns pseudonymous course completion metadata
- `POST /api/certificate/<shield_id>/issue/`
  - issues a new pseudonymous certificate for demo flows

## Notes

- This is an MVP for hackathon demonstration.
- Current passkey gating uses a challenge-based assertion flow suitable for demo purposes; full production WebAuthn registration/assertion lifecycle should be expanded next.
- Dashboard persistence is currently browser-session based (no account auth yet).

## License

MIT - see [LICENSE](LICENSE).
