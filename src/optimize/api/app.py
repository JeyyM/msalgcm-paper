"""FastAPI application for the optimization dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from optimize.api.services.job_manager import job_manager
from optimize.api.services.results_reader import (
    get_convergence,
    get_experiment_detail,
    get_live_solution,
    get_solution,
    get_study_detail,
    list_configs,
    list_experiments,
    list_studies,
    results_root,
)
from optimize.config.loader import load_experiment_config
from optimize.experiments.runner import ExperimentRunner

app = FastAPI(title="MSALGCM Optimize API", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunJobRequest(BaseModel):
    config_path: str
    job_type: str = "experiment"


class TspRunRequest(BaseModel):
    instance: str
    algorithm: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    experiments = list_experiments()
    studies = list_studies()
    jobs = job_manager.list_jobs()
    return {
        "experiments": experiments[:20],
        "studies": studies[:10],
        "active_jobs": [job for job in jobs if job["status"] in {"pending", "running"}],
    }


@app.get("/api/experiments")
def api_list_experiments() -> list[dict]:
    return list_experiments()


@app.get("/api/experiments/{experiment_id}")
def api_get_experiment(experiment_id: str) -> dict:
    try:
        return get_experiment_detail(experiment_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/experiments/{experiment_id}/convergence/{run_id}")
def api_get_convergence(experiment_id: str, run_id: str, downsample: int = 300) -> list[dict]:
    try:
        return get_convergence(experiment_id, run_id, downsample=downsample)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/experiments/{experiment_id}/solutions/{run_id}")
def api_get_solution(experiment_id: str, run_id: str, live: bool = False) -> dict:
    try:
        if live:
            return get_live_solution(experiment_id, run_id)
        return get_solution(experiment_id, run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/experiments/{experiment_id}/solutions/{run_id}/live")
def api_get_live_solution(experiment_id: str, run_id: str) -> dict:
    try:
        return get_live_solution(experiment_id, run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/experiments/{experiment_id}/charts/{chart_name}")
def api_get_chart(experiment_id: str, chart_name: str):
    path = results_root() / experiment_id / "charts" / chart_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="chart not found")
    return FileResponse(path)


@app.get("/api/studies")
def api_list_studies() -> list[dict]:
    return list_studies()


@app.get("/api/studies/{study_id}")
def api_get_study(study_id: str) -> dict:
    try:
        return get_study_detail(study_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/studies/{study_id}/charts/{chart_name}")
def api_get_study_chart(study_id: str, chart_name: str):
    path = results_root() / study_id / "charts" / chart_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="chart not found")
    return FileResponse(path)


@app.get("/api/configs")
def api_list_configs() -> list[dict]:
    return list_configs()


@app.post("/api/configs/validate")
def api_validate_config(body: RunJobRequest) -> dict:
    path = Path(body.config_path)
    if body.job_type == "study":
        from optimize.experiments.study import load_study_config

        load_study_config(path)
        return {"valid": True}
    config = load_experiment_config(path)
    errors = ExperimentRunner().validate(config)
    if errors:
        return {"valid": False, "errors": errors}
    return {"valid": True}


class JspRunRequest(BaseModel):
    instance: str
    algorithm: str


class FsRunRequest(BaseModel):
    instance: str
    algorithm: str


@app.get("/api/domains/tsp")
def api_tsp_catalog() -> dict:
    from optimize.api.services.tsp_catalog import tsp_completion_status

    return tsp_completion_status()


@app.get("/api/domains/tsp/runs")
def api_tsp_runs(instance: str, algorithm: str) -> list[dict]:
    from optimize.api.services.tsp_catalog import list_tsp_runs

    return list_tsp_runs(instance, algorithm)


@app.get("/api/domains/tsp/instances/{instance}/geometry")
def api_tsp_instance_geometry(instance: str) -> dict:
    from optimize.api.services.tsp_catalog import get_tsp_instance_geometry

    try:
        return get_tsp_instance_geometry(instance)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/domains/tsp/run")
def api_start_tsp_run(body: TspRunRequest) -> dict:
    from optimize.api.services.tsp_catalog import TSP_ALGORITHMS, prepare_tsp_launch, write_tsp_config_file

    if body.algorithm not in TSP_ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"unsupported algorithm: {body.algorithm}")
    try:
        prepare_tsp_launch(body.instance, body.algorithm)
        config_path = write_tsp_config_file(body.instance, body.algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    job_id = job_manager.start_experiment(config_path)
    return {"job_id": job_id, "config_path": str(config_path)}


@app.get("/api/domains/scheduling")
def api_jsp_catalog() -> dict:
    from optimize.api.services.jsp_catalog import jsp_completion_status

    return jsp_completion_status()


@app.get("/api/domains/scheduling/runs")
def api_jsp_runs(instance: str, algorithm: str) -> list[dict]:
    from optimize.api.services.jsp_catalog import list_jsp_runs

    return list_jsp_runs(instance, algorithm)


@app.post("/api/domains/scheduling/run")
def api_start_jsp_run(body: JspRunRequest) -> dict:
    from optimize.api.services.jsp_catalog import JSP_ALGORITHMS, prepare_jsp_launch, write_jsp_config_file

    if body.algorithm not in JSP_ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"unsupported algorithm: {body.algorithm}")
    try:
        prepare_jsp_launch(body.instance, body.algorithm)
        config_path = write_jsp_config_file(body.instance, body.algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    job_id = job_manager.start_experiment(config_path)
    return {"job_id": job_id, "config_path": str(config_path)}


@app.get("/api/domains/feature-selection")
def api_fs_catalog() -> dict:
    from optimize.api.services.fs_catalog import fs_completion_status

    return fs_completion_status()


@app.get("/api/domains/feature-selection/runs")
def api_fs_runs(instance: str, algorithm: str) -> list[dict]:
    from optimize.api.services.fs_catalog import list_fs_runs

    return list_fs_runs(instance, algorithm)


@app.post("/api/domains/feature-selection/run")
def api_start_fs_run(body: FsRunRequest) -> dict:
    from optimize.api.services.fs_catalog import FS_ALGORITHMS, prepare_fs_launch, write_fs_config_file

    if body.algorithm not in FS_ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"unsupported algorithm: {body.algorithm}")
    try:
        prepare_fs_launch(body.instance, body.algorithm)
        config_path = write_fs_config_file(body.instance, body.algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    job_id = job_manager.start_experiment(config_path)
    return {"job_id": job_id, "config_path": str(config_path)}


@app.post("/api/jobs/run")
def api_start_job(body: RunJobRequest) -> dict:
    path = Path(body.config_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"config not found: {body.config_path}")

    if body.job_type == "study":
        job_id = job_manager.start_study(path)
    else:
        job_id = job_manager.start_experiment(path)
    return {"job_id": job_id}


@app.get("/api/jobs")
def api_list_jobs() -> list[dict]:
    return job_manager.list_jobs()


@app.get("/api/jobs/{job_id}")
def api_get_job(job_id: str) -> dict:
    progress = job_manager.get(job_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job_id": job_id, **progress.to_dict()}


def mount_frontend(frontend_dist: Path) -> None:
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
