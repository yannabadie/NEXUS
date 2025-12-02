# User Guide

## Prerequisites

Nexus Core relies on external CLI tools to interface with AI models. This approach allows you to use your own accounts and quotas directly.

### 1. Claude Code CLI
Nexus uses `claude` command line tool.
*   **Install**: `npm install -g @anthropic-ai/claude-code`
*   **Auth**: Run `claude auth login` and follow instructions.
*   **Verify**: Run `claude --version` to ensure it is in your PATH.

### 2. Gemini CLI
Nexus uses `gemini` command line tool.
*   **Install**: Follow Google's documentation to install the Gemini CLI.
*   **Auth**: Ensure `gemini` command works and is authenticated.
*   **Models**: Nexus defaults to `gemini-3-pro-preview`. Ensure you have access or change the default in `core/config.py`.

## Running Nexus

### Standard Mode
Ask Nexus to perform a specific task. It will create a swarm, negotiate a plan, and execute it.

```bash
python nexus_core.py "Create a unit test suite for the api module"
```

### Evolution Mode
Ask Nexus to look at a folder and improve it proactively.

```bash
python nexus_core.py --evolve --context ./src
```

## Configuration

You can override defaults using environment variables:

*   `NEXUS_GEMINI_MODEL`: Model ID for Gemini (default: `gemini-3-pro-preview`)
*   `NEXUS_CLAUDE_OPUS`: Model ID for "Lead" tasks (default: `claude-4.5-opus`)
*   `NEXUS_CLAUDE_SONNET`: Model ID for "Worker" tasks (default: `claude-4.5-sonnet`)
*   `GEMINI_CLI_PATH`: Path to binary (default: `gemini`)
*   `CLAUDE_CLI_PATH`: Path to binary (default: `claude`)
