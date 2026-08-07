import { Link } from "react-router-dom";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ALGO_LABELS,
  api,
  JobStatus,
  normalizeTspLiveRoute,
  TspCatalog,
  TspInstanceGeometry,
  TspLiveSolution,
  TspRunRow,
} from "../api";
import { ContextBanner, SectionCard } from "../components/ContextBanner";
import { ConvergenceChart } from "../components/ConvergenceChart";
import { TspRouteChart } from "../components/TspRouteChart";

const ALGORITHMS = [
  "simulated_annealing",
  "tabu_search",
  "particle_swarm",
] as const;

type AlgorithmId = (typeof ALGORITHMS)[number];

function attemptLabel(runId: string | undefined): string | null {
  if (!runId) return null;
  const match = runId.match(/_run_(\d+)$/);
  if (!match) return null;
  return `${Number(match[1])} / 30`;
}

function seedNumber(runId: string | undefined): string {
  if (!runId) return "—";
  const match = runId.match(/_run_(\d+)$/);
  return match ? String(Number(match[1])) : runId;
}

export function TspPage() {
  const [catalog, setCatalog] = useState<TspCatalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [instance, setInstance] = useState("");
  const [algorithm, setAlgorithm] = useState<AlgorithmId>("simulated_annealing");
  const [batchRuns, setBatchRuns] = useState<TspRunRow[]>([]);
  const [starting, setStarting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [liveConvergence, setLiveConvergence] = useState<any[]>([]);
  const [liveSolution, setLiveSolution] = useState<TspLiveSolution | null>(null);
  const [geometry, setGeometry] = useState<TspInstanceGeometry | null>(null);
  const trackedRunIdRef = useRef<string | null>(null);

  const refreshCatalog = useCallback(() => {
    api
      .getTspCatalog()
      .then((data) => {
        setCatalog(data);
        setCatalogError(null);
        if (!instance && data.instances.length) {
          setInstance(data.instances[0].name);
        }
      })
      .catch((error: Error) => {
        setCatalogError(error.message || "Failed to load TSP catalog");
      });
  }, [instance]);

  const refreshRuns = useCallback(() => {
    if (!instance || !algorithm) return;
    api.getTspRuns(instance, algorithm).then(setBatchRuns);
  }, [instance, algorithm]);

  useEffect(() => {
    refreshCatalog();
  }, [refreshCatalog]);

  useEffect(() => {
    refreshRuns();
  }, [refreshRuns]);

  const instanceStatus = useMemo(() => {
    if (!catalog || !instance) return null;
    return catalog.completion[instance]?.[algorithm];
  }, [catalog, instance, algorithm]);

  useEffect(() => {
    if (!instance) return;
    api.getTspGeometry(instance).then(setGeometry).catch(() => setGeometry(null));
  }, [instance]);

  useEffect(() => {
    if (!jobId) return;

    let active = true;

    async function pollJob() {
      const status = await api.getJob(jobId!);
      if (!active) return;
      setJob(status);

      if (status.current_run_id && status.current_run_id !== trackedRunIdRef.current) {
        trackedRunIdRef.current = status.current_run_id;
        setLiveConvergence([]);
        setLiveSolution(null);
      }

      if (status.experiment_dir && status.current_run_id) {
        let latestEvaluations: number | undefined;

        try {
          const points = await api.getConvergence(status.experiment_dir, status.current_run_id);
          if (active) setLiveConvergence(points);
          latestEvaluations = points.at(-1)?.objective_evaluations;
        } catch {
          /* partial file may not exist yet */
        }

        try {
          const solution = await api.getLiveSolution(status.experiment_dir, status.current_run_id);
          if (active) setLiveSolution(solution);
        } catch {
          try {
            const saved = await api.getSolution(status.experiment_dir, status.current_run_id);
            if (active && saved?.route) {
              setLiveSolution({
                live: true,
                objective_evaluations: latestEvaluations,
                current: saved,
              });
            }
          } catch {
            /* no snapshot yet */
          }
        }
      }

      if (status.status === "completed" || status.status === "failed") {
        refreshCatalog();
        refreshRuns();
      }
    }

    pollJob();
    const interval = setInterval(pollJob, 300);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [jobId, refreshCatalog, refreshRuns]);

  const batchComplete = instanceStatus?.done ?? false;
  const isRunning = job?.status === "running";
  const liveAttempt = attemptLabel(job?.current_run_id);

  async function startRun() {
    if (!instance || !algorithm || isRunning) return;
    if (
      batchComplete &&
      !window.confirm("Rerun this experiment? The current 30 results will be replaced.")
    ) {
      return;
    }
    setStarting(true);
    setLiveConvergence([]);
    setLiveSolution(null);
    trackedRunIdRef.current = null;
    try {
      const result = await api.startTspRun(instance, algorithm);
      setJobId(result.job_id);
      setJob(await api.getJob(result.job_id));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to start experiment";
      alert(message);
    } finally {
      setStarting(false);
    }
  }

  const knownOptimum = useMemo(
    () => catalog?.instances.find((item) => item.name === instance)?.known_optimum,
    [catalog, instance],
  );

  const instanceOptions = catalog?.instances ?? [];
  const normalizedLive = normalizeTspLiveRoute(liveSolution);
  const jobLive = normalizeTspLiveRoute(
    job?.live_route
      ? { route: job.live_route, distance: job.live_distance, objective_evaluations: job.live_evaluations }
      : null,
  );
  const liveRoute = jobLive.route ?? normalizedLive.route;
  const liveDistance = jobLive.distance ?? normalizedLive.distance;
  const liveEvaluations =
    job?.live_evaluations ?? normalizedLive.evaluations ?? liveConvergence.at(-1)?.objective_evaluations ?? 0;

  return (
    <div>
      <ContextBanner
        kind="dashboard"
        title="Travelling Salesman Problem"
        meta={["tsp", "n = 30 per instance + algorithm", "SA · TS · PSO"]}
      />

      <SectionCard
        contextLabel={`TSP · ${instance || "…"} · ${ALGO_LABELS[algorithm]}`}
        title="Experiment"
        subtitle="One click runs 30 seeds; rerun replaces the saved results for this pair"
      >
        <div className="launch-row">
          <label className="field-inline">
            <span className="field-label">Instance</span>
            <select
              value={instance}
              onChange={(event) => setInstance(event.target.value)}
              className="wide-select"
              disabled={!instanceOptions.length}
            >
              {instanceOptions.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name}
                  {catalog?.completion[item.name]?.[algorithm]?.done ? " · done" : ""}
                </option>
              ))}
            </select>
          </label>

          <label className="field-inline">
            <span className="field-label">Algorithm</span>
            <select
              value={algorithm}
              onChange={(event) => setAlgorithm(event.target.value as AlgorithmId)}
            >
              {ALGORITHMS.map((item) => (
                <option key={item} value={item}>
                  {ALGO_LABELS[item]}
                  {catalog?.completion[instance]?.[item]?.done ? " · done" : ""}
                </option>
              ))}
            </select>
          </label>

          <button onClick={startRun} disabled={!instance || starting || isRunning}>
            {starting ? "Starting…" : batchComplete ? "Rerun experiment" : "Run experiment"}
          </button>
        </div>

        {catalogError && (
          <p className="status-pending">
            Could not load instances ({catalogError}). Restart the dev server if you recently updated the API.
          </p>
        )}

        {instanceStatus && (
          <div className="status-block muted">
            {instanceStatus.done ? (
              <>
                <p className="status-line">
                  <span className="status-done">Complete</span> · {instanceStatus.successful_runs}/
                  {instanceStatus.target_runs} successful
                  {instanceStatus.best_objective != null && (
                    <> · best tour cost {instanceStatus.best_objective.toFixed(1)}</>
                  )}
                  {instanceStatus.mean_objective != null && (
                    <> · mean {instanceStatus.mean_objective.toFixed(1)}</>
                  )}
                </p>
                {instanceStatus.experiment_id && (
                  <p className="status-line">
                    <Link to={`/experiments/${instanceStatus.experiment_id}`}>Open results</Link>
                  </p>
                )}
              </>
            ) : instanceStatus.experiment_id ? (
              <p className="status-line">
                <span className="status-pending">In progress</span> · {instanceStatus.completed_runs}/
                {instanceStatus.target_runs} seeds finished
              </p>
            ) : (
              <p className="status-line">
                Not started — click <strong>Run experiment</strong> to collect 30 samples.
              </p>
            )}
          </div>
        )}

        {batchRuns.length > 0 && (
          <table className="batch-results-table">
            <thead>
              <tr>
                <th>Seed</th>
                <th>Best objective</th>
                <th>Runtime (s)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {batchRuns.map((row) => (
                <tr key={row.run_id}>
                  <td>{seedNumber(row.run_id)}</td>
                  <td>{row.best_objective != null ? row.best_objective.toFixed(1) : "—"}</td>
                  <td>{row.runtime_seconds != null ? row.runtime_seconds.toFixed(2) : "—"}</td>
                  <td>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </SectionCard>

      {job?.status === "running" && (
        <SectionCard
          contextLabel={`TSP · ${instance} · ${ALGO_LABELS[algorithm]}`}
          title="Running experiment"
          subtitle={job.experiment_dir ? `Saving to ${job.experiment_dir}` : "Starting…"}
        >
          <div className="progress-bar">
            <span style={{ width: `${job.progress_percent}%` }} />
          </div>
          <p className="muted">
            Seed {liveAttempt ?? `${job.completed_runs}/${job.total_runs}`}
            {job.current_best_objective != null ? ` · best so far ${job.current_best_objective.toFixed(1)}` : ""}
          </p>
        </SectionCard>
      )}

      {job?.status === "running" && job.current_run_id && job.experiment_dir && geometry && (
        liveRoute ? (
          <TspRouteChart
            key={`${job.current_run_id}-${liveEvaluations}`}
            contextLabel={`TSP · ${instance} · seed ${liveAttempt ?? "…"}`}
            title="Live tour"
            route={liveRoute}
            coordinates={geometry.coordinates}
            distance={liveDistance}
            evaluations={liveEvaluations}
            knownOptimum={geometry.known_optimum}
          />
        ) : (
          <SectionCard
            contextLabel={`TSP · ${instance}`}
            title="Live tour"
            subtitle={`Seed ${liveAttempt ?? "…"} · waiting for route data`}
          >
            <div className="chart-box chart-empty">
              <p className="muted">Loading tour map…</p>
            </div>
          </SectionCard>
        )
      )}

      {job?.status === "running" && job.current_run_id && job.experiment_dir && (
        <ConvergenceChart
          contextLabel={`TSP · ${instance} · ${ALGO_LABELS[algorithm]}`}
          title="Live convergence"
          subtitle={
            liveConvergence.length
              ? `Seed ${liveAttempt ?? "…"} · solid = best so far · faded = current tour cost`
              : `Seed ${liveAttempt ?? "…"} · collecting data…`
          }
          series={[{ name: `seed-${liveAttempt ?? job.current_run_id}`, data: liveConvergence, color: "#2563eb", showCurrent: true }]}
          referenceObjective={knownOptimum}
          referenceLabel={knownOptimum != null ? `Optimum (${knownOptimum})` : undefined}
        />
      )}
    </div>
  );
}
