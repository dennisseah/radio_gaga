---
title: Radio Gaga
description:
  A command-line healthcare and radiology education assistant powered by Azure
  AI Foundry
---

## Overview

Radio Gaga is a command-line chat application that uses Microsoft Agent
Framework and Azure AI Foundry to provide general healthcare and radiology
education.

The assistant does not replace a qualified healthcare professional. Do not use
it for emergency care, definitive diagnosis, or treatment decisions.

## Requirements

- Python 3.12 or later
- `uv`
- Azure CLI, or another credential supported by `DefaultAzureCredential`
- An Azure AI Foundry project endpoint and model deployment

## Setup

Install the locked dependencies:

```bash
uv sync
```

Copy the sample environment file and set the Foundry values:

```bash
cp .env.sample .env
```

Set `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` in `.env`. The default
session file is `.radio_gaga_session.json`. Set `RADIO_GAGA_SESSION_FILE` to a
different file path when needed.

Authenticate with Azure using the credential available in your environment. For
local development, Azure CLI authentication is supported:

```bash
az login
```

## Run

Start the interactive chat application:

```bash
task run
```

Enter `quit` or `exit` to end the session. Chat history is saved to the
configured session file.

## Development Checks

Run the unit tests, lint checks, and type checks:

```bash
task test:unit
task util:lint
```

Run the dependency security audit:

```bash
task util:pip-audit
```
