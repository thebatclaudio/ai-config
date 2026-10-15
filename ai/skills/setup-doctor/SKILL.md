---
name: setup-doctor
kind: skill
scope: local
description: "Health-check the ai-config installation: .env, generated configs, symlinks, installer. Use when the setup seems broken or after running setup.py."
---

# setup-doctor

Health-check the ai-config installation (`.env`, generated configs, symlinks, installer).

## How to use

Run from the repository root:

```bash
python3 ai/skills/setup-doctor/setup_doctor.py
```

Exit code 1 when unhealthy.

## Used by

- `setup-doctor`
- `/audit-config`
- `/sync`
