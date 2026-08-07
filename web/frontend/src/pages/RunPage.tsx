import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, JobStatus } from "../api";
import { ContextBanner, SectionCard } from "../components/ContextBanner";
import { ConvergenceChart } from "../components/ConvergenceChart";
import { formatExperimentContext, formatJobContext } from "../utils/labels";

export function RunPage() {
  const [configs, setConfigs] = useState<any[]>([]);
  const [configPath, setConfigPath] = useState("");
  const [jobType, setJobType] = useState("experiment");
  const [job, setJob] = useState<JobStatus | null>(null);
  const [liveConvergence, setLiveConvergence] = useState<any[]>([]);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const domainFilter = searchParams.get("domain");
  const filteredDomain = domainFilter === "feature-selection" ? "feature_selection" : domainFilter;

  const visibleConfigs = useMemo(() => {
    const byKind = configs.filter((item) => item.kind === jobType);
    if (!filteredDomain) return byKind;
    return byKind.filter((item) => item.domain === filteredDomain);
  }, [configs, jobType, filteredDomain]);

  const selectedConfig = useMemo(
    () => configs.find((item) => item.path === configPath),
    [configs, configPath],
  );

  useEffect(() => {
    api.listConfigs().then((items) => {
      setConfigs(items);
    });
  }, []);

  useEffect(() => {
    if (!visibleConfigs.length) {
      setConfigPath("");
      return;
    }
    if (!visibleConfigs.some((item) => item.path === configPath)) {
      setConfigPath(visibleConfigs[0].path);
    }
  }, [visibleConfigs, configPath]);

  useEffect(() => {
    const jobId = searchParams.get("job");
    if (!jobId) return;
    const interval = setInterval(async () => {
      const status = await api.getJob(jobId);
      setJob(status);
      if (status.experiment_dir && status.current_run_id) {
        try {
          const points = await api.getConvergence(status.experiment_dir, status.current_run_id);
          setLiveConvergence(points);
        } catch {
          /* run file may not exist yet */
        }
      }
      if (status.status === "completed") {
        clearInterval(interval);
        if (status.experiment_dir) {
          navigate(`/experiments/${status.experiment_dir}`);
        } else if (status.study_dir) {
          navigate(`/studies/${status.study_dir}`);
        }
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [searchParams, navigate]);

  async function startRun() {
    const result = await api.startJob(configPath, jobType);
    navigate(`/run?job=${result.job_id}`);
    setJob(await api.getJob(result.job_id));
  }

  const jobContext = job
    ? formatJobContext({
        job_id: job.job_id,
        experiment_name: job.experiment_name,
        config_path: job.config_path,
        experiment_dir: job.experiment_dir,
        study_dir: job.study_dir,
      })
    : null;

  const liveExperimentContext = job?.experiment_dir
    ? formatExperimentContext({
        id: job.experiment_dir,
        name: job.experiment_name ?? job.experiment_dir,
      })
    : null;

  return (
    <div>
      <ContextBanner
        kind="job"
        title={selectedConfig?.name ?? "Run experiment"}
        meta={[
          jobType === "study" ? "Multi-instance study" : "Single experiment",
          selectedConfig?.domain && selectedConfig?.instance
            ? `${selectedConfig.domain} / ${selectedConfig.instance}`
            : "",
          selectedConfig?.path ?? "",
        ].filter(Boolean)}
      />

      {!searchParams.get("job") && (
        <SectionCard
          contextLabel={selectedConfig ? `${selectedConfig.name} · ${selectedConfig.path}` : "Select a config"}
          title="Launch configuration"
          subtitle="The run will create a new timestamped results folder for this config"
        >
          <div className="launch-row">
            <select value={jobType} onChange={(event) => setJobType(event.target.value)}>
              <option value="experiment">Single experiment</option>
              <option value="study">Multi-instance study</option>
            </select>
            <select value={configPath} onChange={(event) => setConfigPath(event.target.value)} className="wide-select">
              {visibleConfigs.map((item) => (
                <option key={item.path} value={item.path}>
                  {item.name} · {item.path}
                </option>
              ))}
            </select>
            <button onClick={startRun} disabled={!configPath}>Start {selectedConfig?.name ?? "run"}</button>
          </div>
        </SectionCard>
      )}

      {job && jobContext && (
        <SectionCard
          contextLabel={jobContext.fullLabel}
          title={`Job progress · ${job.job_id}`}
          subtitle={job.experiment_dir ? `Writing to ${job.experiment_dir}` : "Preparing output folder"}
        >
          <p>{job.message}</p>
          <div className="progress-bar">
            <span style={{ width: `${job.progress_percent}%` }} />
          </div>
          <p className="muted">
            {job.completed_runs}/{job.total_runs} runs
            {job.current_algorithm ? ` · ${job.current_algorithm}` : ""}
            {job.current_run_id ? ` · ${job.current_run_id}` : ""}
            {job.current_best_objective != null ? ` · best=${job.current_best_objective.toFixed(1)}` : ""}
          </p>
          {job.experiment_dir && (
            <p><Link to={`/experiments/${job.experiment_dir}`}>Open partial results for {job.experiment_dir}</Link></p>
          )}
          {job.study_dir && (
            <p><Link to={`/studies/${job.study_dir}`}>Open study folder {job.study_dir}</Link></p>
          )}
          {job.log.length > 0 && (
            <div className="log-box">
              {job.log.map((line, index) => (
                <div key={index}>{line}</div>
              ))}
            </div>
          )}
        </SectionCard>
      )}

      {liveConvergence.length > 0 && job?.current_run_id && liveExperimentContext && (
        <ConvergenceChart
          contextLabel={`${liveExperimentContext.fullLabel} · ${job.current_run_id}`}
          title={`Live convergence · ${job.current_run_id}`}
          subtitle={`Experiment folder: ${job.experiment_dir}`}
            series={[{ name: job.current_run_id, data: liveConvergence, color: "#2563eb" }]}
        />
      )}
    </div>
  );
}
