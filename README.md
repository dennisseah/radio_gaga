---
title: Radio Gaga
description:
  Command-line healthcare education assistant built with Microsoft Agent
  Framework and Azure AI Foundry
---

## Overview

Radio Gaga is a command-line healthcare education assistant built with Microsoft
Agent Framework and Azure AI Foundry. An Agent Harness coordinator routes health
questions to a specialist health-advisor agent and can call a medical-center
lookup tool when a user asks where a procedure is performed.

For each supported health request, the application displays a structured
execution plan followed by the final answer. It also logs turn duration, tool
calls, delegated-agent calls, and token usage.

> [!WARNING] Radio Gaga provides general educational information. It does not
> replace a qualified healthcare professional and must not be used for emergency
> care, definitive diagnosis, or treatment decisions.

## Features

- Routes medical and health questions through an Agent Harness coordinator
- Delegates health education to a dedicated Azure AI Foundry agent
- Looks up medical centers for supported procedures
- Displays a JSON execution plan that includes completed agent and tool calls
- Persists chat sessions between runs
- Reports latency, tool-call timing, and token usage through application logs
- Rejects unsupported requests and guards against prompt injection

The sample medical-center tool currently recognizes `liver transplant` and
`kidney transplant`. Other procedure names return `No office found`.

## Requirements

- Python 3.12 or later
- [`uv`](https://docs.astral.sh/uv/)
- [Task](https://taskfile.dev/) for the repository shortcuts
- Azure CLI or another credential supported by `DefaultAzureCredential`
- An Azure AI Foundry project with model deployments for the coordinator and
  health-advisor agent

## Setup

Install the project and development dependencies:

```bash
uv sync
```

Create the local environment file:

```bash
cp .env.sample .env
```

Configure these values in `.env`:

| Variable                       | Required | Description                                       |
| ------------------------------ | -------- | ------------------------------------------------- |
| `FOUNDRY_PROJECT_ENDPOINT`     | Yes      | Azure AI Foundry project endpoint                 |
| `HARNESS_FOUNDRY_MODEL`        | Yes      | Model deployment used by the coordinator          |
| `HEALTH_ADVISOR_FOUNDRY_MODEL` | Yes      | Model deployment used by the health-advisor agent |
| `LOG_LEVEL`                    | No       | Python log level; defaults to `INFO`              |
| `RADIO_GAGA_SESSION_FILE`      | No       | Defaults to `.radio_gaga_session.json`            |

Authenticate with a credential supported by `DefaultAzureCredential`. For local
development with Azure CLI, run:

```bash
az login
```

## Run

Start the interactive application with Task:

```bash
task run
```

You can also run the module directly:

```bash
uv run python -m radio_gaga.agent_harness
```

Enter a health question at the `Question:` prompt. Enter `quit` or `exit` to end
the session.

The session is loaded at startup and persisted when the application exits. A
relative `RADIO_GAGA_SESSION_FILE` path is resolved from the repository root. If
a persisted session is invalid, the application quarantines it with an
`.invalid-<identifier>` suffix and starts a new session.

## Development Checks

Run the unit tests with coverage:

```bash
task test:unit
```

Run Ruff and Pyright:

```bash
task util:lint
```

Format the Python source and tests:

```bash
task util:format-code
```

Run the dependency security audit:

```bash
task util:pip-audit
```

Regenerate the exported requirements files after changing dependencies:

```bash
task util:gen-requirements-txt
```
