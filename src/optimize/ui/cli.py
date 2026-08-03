"""Command-line interface."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import typer
from optimize.algorithms.registry import list_algorithms
from optimize.config.loader import load_experiment_config
from optimize.domains.registry import list_domains
from optimize.experiments.runner import ExperimentRunner
from optimize.experiments.study import StudyRunner
from optimize.utilities.logging import setup_logging

app = typer.Typer(
    name="optimize",
    help="Comparative metaheuristic optimization platform",
    no_args_is_help=True,
)


@app.command("run")
def run_experiment(
    config: Path = typer.Option(..., "--config", "-c", help="Experiment JSON config path"),
) -> None:
    """Execute an experiment from a configuration file."""
    setup_logging()
    runner = ExperimentRunner()
    output_dir = runner.run(config)
    typer.echo(f"Experiment complete: {output_dir}")


@app.command("study")
def run_study(
    config: Path = typer.Option(..., "--config", "-c", help="Study JSON config path"),
) -> None:
    """Run a multi-instance study and generate scalability charts."""
    setup_logging()
    study_dir = StudyRunner().run(config)
    typer.echo(f"Study complete: {study_dir}")


@app.command("serve")
def serve_api(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
    with_frontend: bool = typer.Option(False, "--with-frontend"),
) -> None:
    """Start the FastAPI backend for the React dashboard."""
    import uvicorn
    from optimize.api.app import app, mount_frontend

    frontend_dist = Path("web/frontend/dist")
    if with_frontend:
        mount_frontend(frontend_dist)
        typer.echo(f"Dashboard: http://{host}:{port}/")
    else:
        typer.echo(f"API server: http://{host}:{port}/api/health")
        typer.echo("Frontend dev: npm run dev  (from project root)")
    target = "optimize.api.app:app" if reload else app
    uvicorn.run(target, host=host, port=port, reload=reload)


@app.command("dev")
def dev_dashboard(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
) -> None:
    """Start API + React dev servers together (hot reload on both)."""
    root = Path.cwd()
    package_json = root / "package.json"
    frontend_dir = root / "web" / "frontend"

    if not frontend_dir.exists():
        typer.echo("Frontend not found at web/frontend", err=True)
        raise typer.Exit(code=1)

    if package_json.exists() and shutil.which("npm"):
        typer.echo("Starting dashboard dev stack via concurrently...")
        typer.echo(f"  Dashboard: http://localhost:5173")
        typer.echo(f"  API:       http://{host}:{port}/api/health")
        raise typer.Exit(subprocess.call(["npm", "run", "dev"], cwd=root, shell=sys.platform == "win32"))

    if not shutil.which("npm"):
        typer.echo("npm not found. Install Node.js or run: npm install (project root)", err=True)
        raise typer.Exit(code=1)

    typer.echo("Installing root dev dependencies...")
    subprocess.check_call(["npm", "install"], cwd=root, shell=sys.platform == "win32")
    typer.echo("Starting dashboard dev stack...")
    raise typer.Exit(subprocess.call(["npm", "run", "dev"], cwd=root, shell=sys.platform == "win32"))


@app.command("validate")
def validate_config(
    config: Path = typer.Option(..., "--config", "-c", help="Experiment JSON config path"),
) -> None:
    """Validate an experiment configuration without running."""
    experiment = load_experiment_config(config)
    errors = ExperimentRunner().validate(experiment)
    if errors:
        for error in errors:
            typer.echo(f"ERROR: {error}", err=True)
        raise typer.Exit(code=1)
    typer.echo("Configuration is valid.")


@app.command("list")
def list_resources() -> None:
    """List registered domains and algorithms."""
    typer.echo("Domains:")
    for domain in list_domains():
        typer.echo(f"  - {domain}")
    typer.echo("Algorithms:")
    for algorithm in list_algorithms():
        typer.echo(f"  - {algorithm}")


if __name__ == "__main__":
    app()
