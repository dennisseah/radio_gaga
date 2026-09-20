---
title: Radio Gaga
description:
  Command-line healthcare education assistant built with Microsoft Agent
  Framework and Azure AI Foundry
---

## Overview

Radio Gaga is a command-line healthcare education assistant built with Microsoft
Agent Framework and Azure AI Foundry. An Agent Harness coordinator routes health
questions to a specialist health-advisor agent. It can also call a
medical-center lookup tool for supported procedures.

When the health advisor returns a valid plan, the application reconstructs and
displays that plan from completed agent and function calls before printing the
final answer. It also logs turn duration, call timing, delegated-agent usage,
and aggregate token usage.

> replace a qualified healthcare professional and must not be used for emergency
> care, definitive diagnosis, or treatment decisions. [!WARNING] Radio Gaga
> provides general educational information. It does not replace a qualified
> healthcare professional and must not be used for emergency care, definitive
> diagnosis, or treatment decisions. replace a qualified healthcare professional
> and must not be used for emergency care, definitive diagnosis, or treatment
> decisions.

## Features

- Routes medical and health questions through an Agent Harness coordinator
- Delegates health education to a dedicated Azure AI Foundry agent
- Looks up medical centers for supported procedures
- Displays a JSON execution plan assembled from completed agent and function
  calls
- Persists the Agent Framework session between runs
- Reports turn latency, per-call timing, and token usage through application
  logs
- Limits responses to the configured scope and guards against prompt injection

The sample medical-center tool uses exact, case-sensitive matching. It currently
maps `liver transplant` to `Arizona Medical Center` and `kidney transplant` to
`Rocky Mountain Medical Center`. Other values return `No office found`.

## How It Works

1. The Agent Harness coordinator receives a question and selects an available
   tool.
2. The `health_advisor` agent produces a concise JSON plan and executes it in
   the same response for medical or health questions.
3. The `medical_centers` function resolves the location for a supported
   procedure when selected by the coordinator.
4. The execution-plan parser correlates completed function calls and results. It
   uses the health-advisor plan as the base and appends other completed calls as
   plan steps.
5. Middleware records coordinator tool timing and delegated-agent token usage.
6. The application prints the plan when one is available, prints the answer, and
   persists the session when the process exits.

Greetings and scope refusals may not contain an execution plan because they do
not require delegation.

## Requirements

- Python 3.12 or later
- [`uv`](https://docs.astral.sh/uv/)
- [Task](https://taskfile.dev/) for repository shortcuts
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

- `FOUNDRY_PROJECT_ENDPOINT`: Azure AI Foundry project endpoint (required)
- `HARNESS_FOUNDRY_MODEL`: coordinator model deployment (required)
- `HEALTH_ADVISOR_FOUNDRY_MODEL`: health-advisor model deployment (required)
- `LOG_LEVEL`: log level (optional, defaults to `INFO`)
- `RADIO_GAGA_SESSION_FILE`: session file path (optional, defaults to the
  repository root)

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
`.invalid-<identifier>` suffix and starts a fresh session. The default session
file is excluded from Git.

## Project Structure

- `src/radio_gaga/agent_harness.py`: coordinator construction and interactive
  run loop
- `src/radio_gaga/agents/`: delegated specialist agents
- `src/radio_gaga/commons/`: prompts, plan parsing, middleware, and statistics
- `src/radio_gaga/protocols/`: chat-client and session-store interfaces
- `src/radio_gaga/services/`: Foundry client and durable session implementations
- `src/radio_gaga/tools/`: coordinator function tools
- `src/radio_gaga/resources/prompts/`: coordinator and health-advisor prompt
  templates
- `tests/radio_gaga/`: unit tests mirroring the application package layout

## Development Checks

Run the unit tests with coverage:

```bash
task test:unit
```

Run Ruff and Pyright checks:

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
