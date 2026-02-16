import os
import time
import azure.functions as func

from azimg_auditor.pipeline.step1_inventory import run_inventory, to_dicts
from azimg_auditor.report.blob_writer import upload_csv_report
from azimg_auditor.report.findings_writer import upload_findings_csv
from azimg_auditor.governance.engine import evaluate_inventory

app = func.FunctionApp()

SCHEDULE = os.getenv("AZIMG_TIMER_SCHEDULE", "0 0 7 * * *")


@app.timer_trigger(schedule=SCHEDULE, arg_name="mytimer", run_on_startup=False, use_monitor=True)
def azimg_timer(mytimer: func.TimerRequest) -> None:
    start = time.time()

    subs_raw = os.getenv("AZIMG_SUBSCRIPTIONS", "").strip()
    subscriptions = [s.strip() for s in subs_raw.split(",") if s.strip()] if subs_raw else []

    container = os.getenv("AZIMG_STORAGE_CONTAINER", "reports")
    prefix = os.getenv("AZIMG_STORAGE_PREFIX", "vm_inventory/")
    rules_path = os.getenv("AZIMG_RULES_PATH", "azimg_auditor/governance/rules.yaml")

    rows = run_inventory(subscriptions)
    dict_rows = to_dicts(rows)

    inv_blob = upload_csv_report(dict_rows, container=container, prefix=prefix, filename_prefix="vm_inventory")

    findings = evaluate_inventory(dict_rows, rules_path=rules_path)
    findings_blob = upload_findings_csv(findings, container=container, prefix=prefix, filename_prefix="findings")

    duration = round(time.time() - start, 2)
    print(f"[azimg] Inventory uploaded: {inv_blob}")
    print(f"[azimg] Findings uploaded: {findings_blob} findings={len(findings)} duration_s={duration}")