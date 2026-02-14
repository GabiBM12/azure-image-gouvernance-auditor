import os
import time
import azure.functions as func

from azimg_auditor.pipeline.step1_inventory import run_inventory, to_dicts
from azimg_auditor.report.blob_writer import upload_csv_report

app = func.FunctionApp()

@app.function_name(name="azimg_timer")
@app.timer_trigger(schedule="%AZIMG_TIMER_SCHEDULE%", arg_name="mytimer", run_on_startup=False, use_monitor=True)
def azimg_timer(mytimer: func.TimerRequest) -> None:
    start = time.time()

    subs_raw = os.getenv("AZIMG_SUBSCRIPTIONS", "").strip()
    subscriptions = [s.strip() for s in subs_raw.split(",") if s.strip()] if subs_raw else []

    container = os.getenv("AZIMG_STORAGE_CONTAINER", "reports")
    prefix = os.getenv("AZIMG_STORAGE_PREFIX", "vm_inventory/")

    rows = run_inventory(subscriptions)
    dict_rows = to_dicts(rows)

    blob_name = upload_csv_report(dict_rows, container=container, prefix=prefix)

    duration = round(time.time() - start, 2)
    counts = {}
    for r in dict_rows:
        t = r.get("imageType", "unknown")
        counts[t] = counts.get(t, 0) + 1

    print(f"[azimg] Uploaded report: container={container} blob={blob_name}")
    print(f"[azimg] VMs={len(dict_rows)} counts={counts} duration_s={duration}")