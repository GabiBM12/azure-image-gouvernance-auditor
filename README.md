# azure-image-governance-auditor

Milestone 1: Local CLI that inventories VM image usage across subscriptions using Azure Resource Graph.

## Prereqs
- Python 3.10+
- Azure CLI logged in:
  - `az login`
  - (optional) `az account set --subscription <id>`

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .