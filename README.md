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

# Milestone 2 — Azure Function (Serverless Runner)

Milestone 2 turns the local inventory logic into a scheduled Azure-native job.

The inventory now runs as a **Python Azure Function (Linux, Timer trigger)**, deployed via GitHub Actions, using **Managed Identity** and writing reports to Blob Storage.

---

## Architecture

- Azure Function (Python v2, Timer trigger)
- System-assigned Managed Identity
- Azure Blob Storage (report output)
- Application Insights + Log Analytics (observability)
- Terraform for infrastructure
- GitHub Actions (OIDC) for CI/CD

Under the hood, Azure Functions runs the Python code inside a **managed Linux worker**.  
The OS is abstracted away, but runtime characteristics (e.g. glibc version) still matter.

---

## What It Does

On schedule:

1. Queries Azure for VM image data
2. Generates a CSV inventory report
3. Uploads it to Blob Storage (`reports/vm_inventory/`)
4. Emits logs to Application Insights

---

## Deployment

### 1. Provision infra
### 2. Configure GitHub OIDC
Add repo secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_FUNCTIONAPP_NAME`

Push to `main` → CI builds a zip and deploys the Function.

---

## Validate

- Function App → Monitor (see executions)
- Storage Account → `reports` container → CSV file created
- App Insights → Logs (traces + execution output)

---

## Notes

- Deployment uses Run-From-Package (read-only filesystem is expected)
- `AzureWebJobsFeatureFlags=EnableWorkerIndexing` required for Python v2
- `cryptography` must be pinned to a compatible version to avoid GLIBC runtime errors

---

Milestone 2 proves:
- Infrastructure as Code
- Secure identity (no secrets)
- Serverless execution
- Observability-driven debugging
- End-to-end automation