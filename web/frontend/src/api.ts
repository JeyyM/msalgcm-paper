const API = "/api";

export type ExperimentSummary = {
  id: string;
  type: "experiment";
  name: string;
  domain: string;
  instance: string;
  run_count: number;
  completed_runs: number;
};

export type StudySummary = {
  id: string;
  type: "study";
  name: string;
  instance_count: number;
};

export type ComparisonAlgorithmResult = {
  experiment_id: string | null;
  completed_runs: number;
  target_runs: number;
  done: boolean;
  best_objective: number | null;
  mean_objective: number | null;
  std_objective: number | null;
  best_gap_percentage: number | null;
  mean_gap_percentage: number | null;
  mean_runtime_seconds: number | null;
};

export type ComparisonInstanceRow = {
  instance: string;
  problem_size: number | null;
  problem_size_label: string;
  known_optimum: number | null;
  optimum_label: string;
  results: Record<string, ComparisonAlgorithmResult>;
};

export type ComparisonDomainBlock = {
  id: string;
  label: string;
  objective: string;
  evaluation_budget: number;
  target_runs: number;
  instances: ComparisonInstanceRow[];
  algorithms: { id: string; label: string }[];
};

export type ComparisonDashboard = {
  feature_selection_included: boolean;
  feature_selection_note: string;
  algorithms: { id: string; label: string }[];
  domains: ComparisonDomainBlock[];
};

export type TspInstanceGeometry = {
  name: string;
  num_cities: number;
  coordinates: { x: number; y: number }[];
  known_optimum?: number;
};

export type TspSolution = {
  route: number[];
  distance: number;
  known_optimum?: number;
  gap_percentage?: number;
};

export type TspLiveSolution = {
  live?: boolean;
  objective_evaluations?: number;
  current?: TspSolution | null;
  /** Present when a stale API returns a saved solution for a live request. */
  route?: number[];
  distance?: number;
};

export function normalizeTspLiveRoute(payload: TspLiveSolution | TspSolution | null | undefined): {
  route: number[] | null;
  distance?: number;
  evaluations?: number;
} {
  if (!payload) return { route: null };
  if (Array.isArray(payload.route)) {
    return {
      route: payload.route,
      distance: payload.distance,
      evaluations: "objective_evaluations" in payload ? payload.objective_evaluations : undefined,
    };
  }
  const current = payload.current;
  if (current?.route) {
    return {
      route: current.route,
      distance: current.distance,
      evaluations: payload.objective_evaluations,
    };
  }
  return { route: null };
}

export type TspCompletionEntry = {
  experiment_id: string | null;
  completed_runs: number;
  target_runs: number;
  done: boolean;
  can_launch: boolean;
  successful_runs: number;
  failed_runs: number;
  best_objective: number | null;
  mean_objective: number | null;
  best_gap_percentage?: number | null;
  mean_gap_percentage?: number | null;
  mean_runtime_seconds?: number | null;
};

export type TspCatalog = {
  runs_per_experiment: number;
  algorithms: { id: string; label: string }[];
  instances: { name: string; file: string; known_optimum?: number }[];
  completion: Record<string, Record<string, TspCompletionEntry>>;
};

export type DomainInstance = {
  name: string;
  file: string;
  known_optimum?: number;
  jobs?: number;
  machines?: number;
  best_known_makespan?: number | null;
  num_samples?: number;
  num_features?: number;
  discretization?: string;
};

export type DomainCatalog = {
  runs_per_experiment: number;
  algorithms: { id: string; label: string }[];
  launchable_algorithms?: { id: string; label: string }[];
  instances: DomainInstance[];
  completion: Record<string, Record<string, TspCompletionEntry>>;
};

export type JspOperation = {
  job: number;
  operation_index?: number;
  machine: number;
  processing_time: number;
  start: number;
  finish?: number;
};

export type JspSchedule = {
  instance?: string;
  makespan: number;
  operations: JspOperation[];
  known_optimum?: number;
  gap_percentage?: number;
};

export type JspLiveSolution = {
  live?: boolean;
  objective_evaluations?: number;
  current?: JspSchedule | null;
  makespan?: number;
  operations?: JspOperation[];
};

export function normalizeJspLiveSchedule(payload: JspLiveSolution | JspSchedule | null | undefined): {
  operations: JspOperation[];
  makespan?: number;
  evaluations?: number;
} {
  if (!payload) return { operations: [] };
  if (Array.isArray(payload.operations)) {
    return {
      operations: payload.operations,
      makespan: payload.makespan,
      evaluations: "objective_evaluations" in payload ? payload.objective_evaluations : undefined,
    };
  }
  const current = payload.current;
  if (current?.operations) {
    return {
      operations: current.operations,
      makespan: current.makespan,
      evaluations: payload.objective_evaluations,
    };
  }
  return { operations: [] };
}

export function normalizeFsLiveSolution(payload: FsLiveSolution | FsSchedule | null | undefined): {
  featureMask: number[];
  featureNames?: string[];
  selectedCount?: number;
  totalFeatures?: number;
  cvScore?: number;
  testScore?: number;
} {
  if (!payload) return { featureMask: [] };

  const schedule = "feature_mask" in payload ? payload : payload.current;
  if (!schedule?.feature_mask) return { featureMask: [] };

  return {
    featureMask: schedule.feature_mask.map((value) => (value ? 1 : 0)),
    featureNames: schedule.feature_mask.map((_, index) => `F${index + 1}`),
    selectedCount: schedule.selected_feature_count,
    totalFeatures: schedule.feature_mask.length,
    cvScore: schedule.cv_score,
    testScore: schedule.test_score,
  };
}

export type FsSchedule = {
  instance?: string;
  feature_mask: number[];
  selected_feature_names?: string[];
  selected_feature_count?: number;
  cv_score?: number;
  test_score?: number;
  objective_value?: number;
};

export type FsLiveSolution = {
  live?: boolean;
  objective_evaluations?: number;
  current?: FsSchedule | null;
};

export type DomainRunRow = TspRunRow;

export type TspRunRow = {
  experiment_id: string;
  run_id: string;
  seed?: string;
  status?: string;
  best_objective: number | null;
  runtime_seconds: number | null;
};

export type JobStatus = {
  job_id: string;
  status: string;
  job_type: string;
  experiment_name?: string;
  config_path?: string;
  progress_percent: number;
  current_algorithm?: string;
  current_run_id?: string;
  completed_runs: number;
  total_runs: number;
  current_best_objective?: number;
  experiment_dir?: string;
  study_dir?: string;
  message: string;
  error?: string;
  log: string[];
  live_route?: number[];
  live_distance?: number;
  live_evaluations?: number;
};

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  let lastError: Error | null = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(url, init);
      if (!response.ok) {
        const body = await response.text();
        const retryable = response.status >= 500 || response.status === 429;
        if (retryable && attempt < 2) {
          await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
          continue;
        }
        throw new Error(body || `Request failed (${response.status})`);
      }
      return response.json();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error("Request failed");
      if (attempt < 2) {
        await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
        continue;
      }
    }
  }
  throw lastError ?? new Error("Request failed");
}

const TSP_COMPARISON_INSTANCES = ["eil51", "berlin52", "st70", "kroA100", "ch130", "rat195"];
const TSP_CITY_COUNTS: Record<string, number> = {
  eil51: 51,
  berlin52: 52,
  st70: 70,
  kroA100: 100,
  ch130: 130,
  rat195: 195,
};
const COMPARISON_ALGORITHMS = ["simulated_annealing", "tabu_search", "particle_swarm"] as const;

function mapCompletionEntry(
  entry: TspCompletionEntry | undefined,
  targetRuns: number,
): ComparisonAlgorithmResult {
  return {
    experiment_id: entry?.experiment_id ?? null,
    completed_runs: entry?.completed_runs ?? 0,
    target_runs: entry?.target_runs ?? targetRuns,
    done: entry?.done ?? false,
    best_objective: entry?.best_objective ?? null,
    mean_objective: entry?.mean_objective ?? null,
    std_objective: null,
    best_gap_percentage: entry?.best_gap_percentage ?? null,
    mean_gap_percentage: entry?.mean_gap_percentage ?? null,
    mean_runtime_seconds: entry?.mean_runtime_seconds ?? null,
  };
}

async function buildComparisonFromCatalogs(): Promise<ComparisonDashboard> {
  const [tsp, jsp] = await Promise.all([
    fetchJson<TspCatalog>(`${API}/domains/tsp`),
    fetchJson<DomainCatalog>(`${API}/domains/scheduling`),
  ]);

  const tspInstances = tsp.instances.filter((item) => TSP_COMPARISON_INSTANCES.includes(item.name));
  const jspInstances = jsp.instances;

  return {
    feature_selection_included: false,
    feature_selection_note: "Feature Selection omitted — PSO comparison runs still in progress.",
    algorithms: tsp.algorithms,
    domains: [
      {
        id: "tsp",
        label: "Travelling Salesman Problem",
        objective: "minimize tour length",
        evaluation_budget: 100_000,
        target_runs: tsp.runs_per_experiment,
        instances: tspInstances.map((item) => ({
          instance: item.name,
          problem_size: TSP_CITY_COUNTS[item.name] ?? null,
          problem_size_label: TSP_CITY_COUNTS[item.name]
            ? `${TSP_CITY_COUNTS[item.name]} cities`
            : item.name,
          known_optimum: item.known_optimum ?? null,
          optimum_label: "Known optimum",
          results: Object.fromEntries(
            COMPARISON_ALGORITHMS.map((alg) => [
              alg,
              mapCompletionEntry(tsp.completion[item.name]?.[alg], tsp.runs_per_experiment),
            ]),
          ),
        })),
        algorithms: tsp.algorithms,
      },
      {
        id: "jsp",
        label: "Job Shop Scheduling",
        objective: "minimize makespan",
        evaluation_budget: 50_000,
        target_runs: jsp.runs_per_experiment,
        instances: jspInstances.map((item) => ({
          instance: item.name,
          problem_size: item.jobs ?? null,
          problem_size_label:
            item.jobs != null && item.machines != null ? `${item.jobs}×${item.machines}` : item.name,
          known_optimum: item.best_known_makespan ?? item.known_optimum ?? null,
          optimum_label: "Best known makespan",
          results: Object.fromEntries(
            COMPARISON_ALGORITHMS.map((alg) => [
              alg,
              mapCompletionEntry(jsp.completion[item.name]?.[alg], jsp.runs_per_experiment),
            ]),
          ),
        })),
        algorithms: jsp.algorithms,
      },
    ],
  };
}

async function enrichComparisonWithRuntimes(dashboard: ComparisonDashboard): Promise<ComparisonDashboard> {
  const domains = await Promise.all(
    dashboard.domains.map(async (domain) => {
      const instances = await Promise.all(
        domain.instances.map(async (row) => {
          const results = { ...row.results };
          await Promise.all(
            COMPARISON_ALGORITHMS.map(async (alg) => {
              const result = results[alg];
              if (result?.mean_runtime_seconds != null || result?.completed_runs === 0) {
                return;
              }
              const runsPath =
                domain.id === "tsp"
                  ? `${API}/domains/tsp/runs?instance=${encodeURIComponent(row.instance)}&algorithm=${encodeURIComponent(alg)}`
                  : `${API}/domains/scheduling/runs?instance=${encodeURIComponent(row.instance)}&algorithm=${encodeURIComponent(alg)}`;
              try {
                const runs = await fetchJson<TspRunRow[]>(runsPath);
                const runtimes = runs
                  .filter((item) => item.status === "completed" && item.runtime_seconds != null)
                  .map((item) => item.runtime_seconds as number);
                if (runtimes.length) {
                  results[alg] = {
                    ...result,
                    mean_runtime_seconds: runtimes.reduce((sum, value) => sum + value, 0) / runtimes.length,
                  };
                }
              } catch {
                /* runs endpoint may 404 for empty batches */
              }
            }),
          );
          return { ...row, results };
        }),
      );
      return { ...domain, instances };
    }),
  );
  return { ...dashboard, domains };
}

async function loadComparisonDashboard(): Promise<ComparisonDashboard> {
  let dashboard: ComparisonDashboard | null = null;
  try {
    dashboard = await fetchJson<ComparisonDashboard>(`${API}/dashboard/comparison`);
  } catch {
    /* newer route may be unavailable on an older API process */
  }
  if (!dashboard) {
    try {
      const dash = await fetchJson<{ comparison?: ComparisonDashboard }>(`${API}/dashboard`);
      dashboard = dash.comparison ?? null;
    } catch {
      /* fall through */
    }
  }
  if (!dashboard) {
    dashboard = await buildComparisonFromCatalogs();
  }
  return enrichComparisonWithRuntimes(dashboard);
}

export const api = {
  dashboard: () =>
    fetchJson<{
      experiments: ExperimentSummary[];
      studies: StudySummary[];
      active_jobs: JobStatus[];
      comparison?: ComparisonDashboard;
    }>(`${API}/dashboard`),
  comparisonDashboard: () => loadComparisonDashboard(),
  listExperiments: () => fetchJson<ExperimentSummary[]>(`${API}/experiments`),
  getExperiment: (id: string) => fetchJson<any>(`${API}/experiments/${id}`),
  getConvergence: (experimentId: string, runId: string) =>
    fetchJson<any[]>(`${API}/experiments/${experimentId}/convergence/${runId}?downsample=400`),
  getSolution: (experimentId: string, runId: string) =>
    fetchJson<any>(`${API}/experiments/${experimentId}/solutions/${runId}`),
  getLiveSolution: (experimentId: string, runId: string) =>
    fetchJson<TspLiveSolution>(
      `${API}/experiments/${experimentId}/solutions/${encodeURIComponent(runId)}/live`,
    ),
  getStudy: (id: string) => fetchJson<any>(`${API}/studies/${id}`),
  getTspCatalog: () => fetchJson<TspCatalog>(`${API}/domains/tsp`),
  getTspGeometry: (instance: string) =>
    fetchJson<TspInstanceGeometry>(`${API}/domains/tsp/instances/${encodeURIComponent(instance)}/geometry`),
  getTspRuns: (instance: string, algorithm: string) =>
    fetchJson<TspRunRow[]>(`${API}/domains/tsp/runs?instance=${encodeURIComponent(instance)}&algorithm=${encodeURIComponent(algorithm)}`),
  startTspRun: (instance: string, algorithm: string) =>
    fetchJson<{ job_id: string; config_path: string }>(`${API}/domains/tsp/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instance, algorithm }),
    }),
  getJspCatalog: () => fetchJson<DomainCatalog>(`${API}/domains/scheduling`),
  getJspRuns: (instance: string, algorithm: string) =>
    fetchJson<DomainRunRow[]>(
      `${API}/domains/scheduling/runs?instance=${encodeURIComponent(instance)}&algorithm=${encodeURIComponent(algorithm)}`,
    ),
  startJspRun: (instance: string, algorithm: string) =>
    fetchJson<{ job_id: string; config_path: string }>(`${API}/domains/scheduling/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instance, algorithm }),
    }),
  getJspLiveStatus: (instance: string, algorithm: string) =>
    fetchJson<JobStatus>(
      `${API}/domains/scheduling/live-status?instance=${encodeURIComponent(instance)}&algorithm=${encodeURIComponent(algorithm)}`,
    ),
  getFsCatalog: () => fetchJson<DomainCatalog>(`${API}/domains/feature-selection`),
  getFsRuns: (instance: string, algorithm: string) =>
    fetchJson<DomainRunRow[]>(
      `${API}/domains/feature-selection/runs?instance=${encodeURIComponent(instance)}&algorithm=${encodeURIComponent(algorithm)}`,
    ),
  startFsRun: (instance: string, algorithm: string) =>
    fetchJson<{ job_id: string; config_path: string }>(`${API}/domains/feature-selection/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instance, algorithm }),
    }),
  getFsLiveStatus: (instance: string, algorithm: string) =>
    fetchJson<JobStatus>(
      `${API}/domains/feature-selection/live-status?instance=${encodeURIComponent(instance)}&algorithm=${encodeURIComponent(algorithm)}`,
    ),
  listConfigs: () => fetchJson<any[]>(`${API}/configs`),
  startJob: (config_path: string, job_type: string) =>
    fetchJson<{ job_id: string }>(`${API}/jobs/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config_path, job_type }),
    }),
  getJob: (jobId: string) => fetchJson<JobStatus>(`${API}/jobs/${jobId}`),
  chartUrl: (experimentId: string, chartName: string) =>
    `${API}/experiments/${experimentId}/charts/${chartName}`,
  studyChartUrl: (studyId: string, chartName: string) =>
    `${API}/studies/${studyId}/charts/${chartName}`,
};

export const ALGO_LABELS: Record<string, string> = {
  simulated_annealing: "Simulated Annealing",
  tabu_search: "Tabu Search",
  particle_swarm: "Particle Swarm",
};
