# Dynamic Agent Architecture

Nexus Core does not rely on a static list of agents. Instead, it generates an **Architecture Plan** for each significant task.

## The Process

1.  **Task Analysis**: The system analyzes the user request and the project context.
2.  **Debate Phase**: Two core agents (typically representing "Analysis" and "Action") debate the best approach.
    *   *Agent A*: "This looks like a simple bug fix. One agent is enough."
    *   *Agent B*: "Wait, this touches the payment gateway. We need a separate Reviewer agent for safety."
3.  **Plan Definition**: They produce a JSON `ArchitecturePlan` defining:
    *   **Modes**: `parallel`, `sequential`, `hierarchical`, `specialist`.
    *   **Roles**: Custom roles generated on the fly (e.g., "SecurityAuditor", "ReactRefactorer").
    *   **Workflow**: How data flows between agents.

## Agent Types

While roles are dynamic, they usually map to underlying model tiers:

*   **Architect / Lead**: Uses high-reasoning models (Claude 4.5 Opus, Gemini 3 Pro). Responsible for planning and review.
*   **Engineer / Builder**: Uses balanced models (Claude 4.5 Sonnet). Writes the bulk of the code.
*   **Fast / Tool User**: Uses low-latency models (Gemini Flash). Handles search, simple edits, and lookups.

## Example Plan

```json
{
  "mode": "lead_support",
  "rationale": "High-risk change requires double-check.",
  "workflow": "Engineer implements -> Lead reviews",
  "agents": [
    {
      "id": "LeadArchitect",
      "model": "claude-4.5-opus",
      "role": "Review and Approval",
      "tools": ["read_file", "review_diff"]
    },
    {
      "id": "BackendEngineer",
      "model": "claude-4.5-sonnet",
      "role": "Implementation",
      "tools": ["read", "write", "test"]
    }
  ]
}
```
