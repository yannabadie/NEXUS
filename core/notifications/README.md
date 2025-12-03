# Notifications Module

System alerts and reporting for NEXUS V7.5.

## Overview

Handles user communication outside the REPL loop.

## Channels

### 1. File Notifications (`PENDING_REVIEW.md`)
Generated after an `/evolve` cycle completes. Lists the created children, their mutations, and their **Fitness Score** impact (formerly ASI Score).

### 2. Email (`email_notifier.py`)
(Optional) Sends alerts via SMTP when long-running tasks complete.

### 3. REPL Alerts (`repl_alert.py`)
Immediate visual feedback in the console for critical events (Stagnation, Panic).