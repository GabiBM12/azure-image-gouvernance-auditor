import typer

from azimg_auditor.config import load_config
from azimg_auditor.pipeline.step1_inventory import run_inventory, to_dicts
from azimg_auditor.report.writers import write_csv

app = typer.Typer(no_args_is_help=True)

@app.command()
def inventory(out: str = typer.Option("out/vm_inventory.csv", "--out")):
    """Inventory VM image references across subscriptions using Azure Resource Graph."""
    cfg = load_config()
    rows = run_inventory(cfg.subscriptions)
    write_csv(out, to_dicts(rows))
    typer.echo(f"✅ Inventory complete: {out} ({len(rows)} VM(s))")

if __name__ == "__main__":
    app()