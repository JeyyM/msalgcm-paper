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
};

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const api = {
  dashboard: () => fetchJson<{ experiments: ExperimentSummary[]; studies: StudySummary[]; active_jobs: JobStatus[] }>(`${API}/dashboard`),
  listExperiments: () => fetchJson<ExperimentSummary[]>(`${API}/experiments`),
  getExperiment: (id: string) => fetchJson<any>(`${API}/experiments/${id}`),
  getConvergence: (experimentId: string, runId: string) =>
    fetchJson<any[]>(`${API}/experiments/${experimentId}/convergence/${runId}?downsample=400`),
  getSolution: (experimentId: string, runId: string) =>
    fetchJson<any>(`${API}/experiments/${experimentId}/solutions/${runId}`),
  getStudy: (id: string) => fetchJson<any>(`${API}/studies/${id}`),
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
