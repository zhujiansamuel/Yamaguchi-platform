"""CLI tool for iPhone Device Farm."""

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

import httpx

app = typer.Typer(name="iphone-farm", help="iPhone Device Farm CLI")
console = Console()

BASE_URL = "http://localhost:8000"


def _get(path: str) -> dict:
    with httpx.Client(base_url=BASE_URL) as client:
        resp = client.get(path)
        resp.raise_for_status()
        return resp.json()


def _post(path: str, data: dict) -> dict:
    with httpx.Client(base_url=BASE_URL) as client:
        resp = client.post(path, json=data)
        resp.raise_for_status()
        return resp.json()


# --- Device commands ---

@app.command()
def devices():
    """List all devices."""
    data = _get("/api/devices")
    table = Table(title="Devices")
    table.add_column("UDID", style="cyan")
    table.add_column("Name")
    table.add_column("Model")
    table.add_column("iOS")
    table.add_column("Status")
    for d in data:
        status_style = "green" if d["status"] == "connected" else "red"
        table.add_row(d["udid"][:12] + "...", d["name"], d["model"], d["ios_version"],
                      f"[{status_style}]{d['status']}[/{status_style}]")
    console.print(table)


@app.command()
def apps(udid: str):
    """List apps installed on a device."""
    data = _get(f"/api/devices/{udid}/apps")
    table = Table(title=f"Apps on {udid[:12]}...")
    table.add_column("Bundle ID", style="cyan")
    table.add_column("Name")
    for bundle_id, info in data.items():
        name = info.get("CFBundleDisplayName", info.get("CFBundleName", ""))
        table.add_row(bundle_id, name)
    console.print(table)


# --- Task commands ---

@app.command()
def run(
    script: str = typer.Argument(help="Script name (without .py)"),
    name: str = typer.Option(None, "--name", "-n", help="Task name"),
    target: str = typer.Option("all", "--target", "-t", help="Device UDID or 'all'"),
    args: Optional[str] = typer.Option(None, "--args", "-a", help="JSON args for the script"),
):
    """Submit a task to run a script on devices."""
    task_name = name or f"Run {script}"
    target_devices = target if target == "all" else [t.strip() for t in target.split(",")]
    script_args = json.loads(args) if args else None

    result = _post("/api/tasks", {
        "name": task_name,
        "script_name": script,
        "script_args": script_args,
        "target_devices": target_devices,
    })
    console.print(f"[green]Submitted {result['count']} task(s)[/green]: IDs {result['task_ids']}")


@app.command()
def tasks(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l"),
):
    """List tasks."""
    params = f"?limit={limit}"
    if status:
        params += f"&status={status}"
    data = _get(f"/api/tasks{params}")

    table = Table(title="Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Script")
    table.add_column("Device")
    table.add_column("Status")
    table.add_column("Created")
    for t in data:
        status_style = {
            "completed": "green", "failed": "red", "running": "yellow",
            "queued": "blue", "pending": "dim",
        }.get(t["status"], "")
        device = (t["device_udid"] or "")[:12]
        table.add_row(
            str(t["id"]), t["name"], t["script_name"], device,
            f"[{status_style}]{t['status']}[/{status_style}]", t["created_at"][:19],
        )
    console.print(table)


@app.command()
def task(task_id: int):
    """Get details of a specific task."""
    data = _get(f"/api/tasks/{task_id}")
    console.print_json(json.dumps(data, indent=2))


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
):
    """Start the device farm server."""
    import uvicorn
    uvicorn.run("app.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
