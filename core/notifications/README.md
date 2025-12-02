# Notifications Module

Alert and notification system for NEXUS V7.

## Overview

Provides multiple notification channels:
- **File notifications** (PENDING_REVIEW.md)
- **Email notifications** (Outlook SMTP)
- **REPL alerts** (in-session)

## Files

| File | Purpose | Key Classes |
|------|---------|-------------|
| `file_notifier.py` | File-based notifications | `create_pending_review()` |
| `email_notifier.py` | Email notifications | `EmailNotifier` |
| `repl_alert.py` | In-session alerts | `show_alert()` |
| `__init__.py` | Module exports | - |

## Key Functions

### File Notifications

```python
from core.notifications import create_pending_review
from datetime import datetime

path = create_pending_review(
    workspace_path=Path("./workspace"),
    generation=7,
    children=[
        {"id": "CHILD_001", "score": 0.81, "improvement": 0.03}
    ],
    created_at=datetime.now()
)
# Creates: workspace/PENDING_REVIEW.md
```

### Email Notifications

```python
from core.notifications import EmailNotifier

notifier = EmailNotifier()
notifier.send_evolution_complete(
    generation=7,
    winner_id="CHILD_001",
    improvement_pct=3.8
)
```

## Configuration

```bash
# Email (Outlook SMTP)
EMAIL_ENABLED=True
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_FROM=user@outlook.com
EMAIL_TO=user@outlook.com
NEXUS_EMAIL_PASSWORD=...
```

## Notification Types

| Type | Channel | Trigger |
|------|---------|---------|
| Evolution complete | File, Email | `/evolve` finishes |
| Child ready for review | File | Child passes validation |
| Panic triggered | REPL | Fatal error |
| Stagnation warning | REPL | 3+ generations without improvement |

## See Also

- [Core README](../README.md) - Architecture overview
- [Evolution Module](../evolution/README.md) - Evolution triggers
