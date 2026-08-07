import { Link } from "react-router-dom";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ALGO_LABELS,
  api,
  DomainCatalog,
  DomainRunRow,
  JobStatus,
  JspLiveSolution,
  normalizeJspLiveSchedule,
} from "../api";
import { ContextBanner, SectionCard } from "../components/ContextBanner";
import { ConvergenceChart } from "../components/ConvergenceChart";
import { JspGanttChart } from "../components/JspGanttChart";

const ALGORITHMS = [
  "simulated_annealing",
  "tabu_search",
  "particle_swarm",
] as const;

type AlgorithmId = (typeof ALGORITHMS)[number];

function attemptLabel(runId: string | undefined, totalRuns: number): string | null {
  if (!runId) return null;
  const match = runId.match(/_run_(\d+)$/);
  if (!match) return null;
  return `${Number(match[1])} / ${totalRuns}`;
}

function seedNumber(runId: string | undefined): string {
  if (!runId) return "—";
  const match = runId.match(/_run_(\d+)$/);
  return match ? String(Number(match[1])) : runId;
}

function instanceLabel(item: DomainCatalog["instances"][number]): string {
  const size =
    item.jobs != null && item.machines != null ? `${item.jobs}×${item.machines}` : "";
  return size ? `${item.name} (${size})` : item.name;
}

export function JspPage() {
  const [catalog, setCatalog] = useState<DomainCatalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [instance, setInstance] = useState("");
  const [algorithm, setAlgorithm] = useState<AlgorithmId>("simulated_annealing");
  const [batchRuns, setBatchRuns] = useState<DomainRunRow[]>([]);
  const [starting, setStarting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [liveConvergence, setLiveConvergence] = useState<any[]>([]);
  const [liveSchedule, setLiveSchedule] = useState<JspLiveSolution | null>(null);
  const trackedRunIdRef = useRef<string | null>(null);

  const targetRuns = catalog?.runs_per_experiment ?? 30;

  const refreshCatalog = useCallback(() => {
    api
      .getJspCatalog()
      .then((data) => {
        setCatalog(data);
        setCatalogError(null);
        if (!instance && data.instances.length) {
          setInstance(data.instances[0].name);
        }
      })
      .catch((error: Error) => {
        setCatalogError(error.message || "Failed to load JSP catalog");
      });
  }, [instance]);

  const refreshRuns = useCallback(() => {
    if (!instance || !algorithm) return;
    api.getJspRuns(instance, algorithm).then(setBatchRuns);
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
    if (!jobId) return;

    let active = true;

    async function pollJob() {
      const status = await api.getJob(jobId!);
      if (!active) return;
      setJob(status);

      if (status.current_run_id && status.current_run_id !== trackedRunIdRef.current) {
        trackedRunIdRef.current = status.current_run_id;
        setLiveConvergence([]);
        setLiveSchedule(null);
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
          if (active) setLiveSchedule(solution);
        } catch {
          try {
            const saved = await api.getSolution(status.experiment_dir, status.current_run_id);
            if (active && saved?.operations) {
              setLiveSchedule({
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

  // Show live Gantt/convergence for in-progress batches even after a page refresh
  // or when started via script — no in-memory job id in those cases.
  useEffect(() => {
    if (jobId) return;
    if (!instance || !algorithm) return;

    let active = true;
    let lastSeenCompletedRuns = -1;

    async function pollExternal() {
      try {
        const status = await api.getJspLiveStatus(instance, algorithm);
        if (!active) return;
        setJob(status);

        if (status.current_run_id && status.current_run_id !== trackedRunIdRef.current) {
          trackedRunIdRef.current = status.current_run_id;
          setLiveConvergence([]);
          setLiveSchedule(null);
        }
        if (status.completed_runs !== lastSeenCompletedRuns) {
          lastSeenCompletedRuns = status.completed_runs;
          refreshRuns();
          refreshCatalog();
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
            if (active) setLiveSchedule(solution);
          } catch {
            try {
              const saved = await api.getSolution(status.experiment_dir, status.current_run_id);
              if (active && saved?.operations) {
                setLiveSchedule({
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
      } catch {
        if (active) {
          setJob((current) => (current?.job_id === "external" ? null : current));
          if (lastSeenCompletedRuns >= 0) {
            refreshCatalog();
            refreshRuns();
          }
        }
      }
    }

    pollExternal();
    const interval = setInterval(pollExternal, 1000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [jobId, instance, algorithm, refreshCatalog, refreshRuns]);

  const batchComplete = instanceStatus?.done ?? false;
  const isRunning = job?.status === "running";
  const liveAttempt = attemptLabel(job?.current_run_id, targetRuns);

  async function startRun() {
    if (!instance || !algorithm || isRunning) return;
    if (
      batchComplete &&
      !window.confirm(`Rerun this experiment? The current ${targetRuns} results will be replaced.`)
    ) {
      return;
    }
    setStarting(true);
    setLiveConvergence([]);
    setLiveSchedule(null);
    trackedRunIdRef.current = null;
    try {
      const result = await api.startJspRun(instance, algorithm);
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
  const normalizedLive = normalizeJspLiveSchedule(liveSchedule);
  const liveOperations = normalizedLive.operations;
  const liveMakespan =
    normalizedLive.makespan ??
    liveConvergence.at(-1)?.best_objective ??
    job?.current_best_objective ??
    0;
  const liveEvaluations =
    normalizedLive.evaluations ?? liveConvergence.at(-1)?.objective_evaluations ?? 0;

  return (
    <div>
      <ContextBanner
        kind="dashboard"
        title="Job Scheduling"
        meta={["scheduling", `n = ${targetRuns} per instance + algorithm`, "SA · TS · PSO"]}
      />

      <SectionCard
        contextLabel={`JSP · ${instance || "…"} · ${ALGO_LABELS[algorithm]}`}
        title="Experiment"
        subtitle={`One click runs ${targetRuns} seeds; rerun replaces the saved results for this pair`}
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
                  {instanceLabel(item)}
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
                    <> · best makespan {instanceStatus.best_objective.toFixed(0)}</>
                  )}
                  {instanceStatus.mean_objective != null && (
                    <> · mean {instanceStatus.mean_objective.toFixed(0)}</>
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
                Not started — click <strong>Run experiment</strong> to collect {targetRuns} samples.
              </p>
            )}
          </div>
        )}

        {batchRuns.length > 0 && (
          <table className="batch-results-table">
            <thead>
              <tr>
                <th>Seed</th>
                <th>Best makespan</th>
                <th>Runtime (s)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {batchRuns.map((row) => (
                <tr key={row.run_id}>
                  <td>{seedNumber(row.run_id)}</td>
                  <td>{row.best_objective != null ? row.best_objective.toFixed(0) : "—"}</td>
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
          contextLabel={`JSP · ${instance} · ${ALGO_LABELS[algorithm]}`}
          title="Running experiment"
          subtitle={job.experiment_dir ? `Saving to ${job.experiment_dir}` : "Starting…"}
        >
          <div className="progress-bar">
            <span style={{ width: `${job.progress_percent}%` }} />
          </div>
          <p className="muted">
            Seed {liveAttempt ?? `${job.completed_runs}/${job.total_runs}`}
            {job.current_best_objective != null
              ? ` · best makespan so far ${job.current_best_objective.toFixed(0)}`
              : ""}
          </p>
        </SectionCard>
      )}

      {job?.status === "running" && job.current_run_id && job.experiment_dir && (
        liveOperations.length > 0 ? (
          <JspGanttChart
            key={`${job.current_run_id}-${liveEvaluations}`}
            contextLabel={`JSP · ${instance} · seed ${liveAttempt ?? "…"}`}
            title="Live schedule"
            operations={liveOperations}
            makespan={liveMakespan}
            evaluations={liveEvaluations}
            knownOptimum={knownOptimum}
          />
        ) : (
          <SectionCard
            contextLabel={`JSP · ${instance}`}
            title="Live schedule"
            subtitle={`Seed ${liveAttempt ?? "…"} · waiting for Gantt data`}
          >
            <div className="chart-box chart-empty">
              <p className="muted">Loading schedule…</p>
            </div>
          </SectionCard>
        )
      )}

      {job?.status === "running" && job.current_run_id && job.experiment_dir && (
        <ConvergenceChart
          contextLabel={`JSP · ${instance} · ${ALGO_LABELS[algorithm]}`}
          title="Live convergence"
          subtitle={
            liveConvergence.length
              ? `Seed ${liveAttempt ?? "…"} · best makespan so far`
              : `Seed ${liveAttempt ?? "…"} · collecting data…`
          }
          series={[
            {
              name: `seed-${liveAttempt ?? job.current_run_id}`,
              data: liveConvergence,
              color: "#059669",
              showCurrent: true,
            },
          ]}
          referenceObjective={knownOptimum}
          referenceLabel={knownOptimum != null ? `Best known (${knownOptimum})` : undefined}
        />
      )}
    </div>
  );
}
