import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { api, ExperimentSummary, StudySummary } from "../api";
import { ContextBanner, SectionCard } from "../components/ContextBanner";

export function ResultsDashboardPage() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [studies, setStudies] = useState<StudySummary[]>([]);
  const [activeJobs, setActiveJobs] = useState<any[]>([]);

  useEffect(() => {
    api.dashboard().then((data) => {
      setExperiments(data.experiments);
      setStudies(data.studies);
      setActiveJobs(data.active_jobs);
    });
  }, []);

  return (
    <div>
      <ContextBanner
        kind="dashboard"
        title="Results Dashboard"
        meta={["All domains", "Experiments and scalability studies"]}
      />

      {activeJobs.length > 0 && (
        <SectionCard contextLabel="Active jobs" title="Running now" subtitle="Each job links to its experiment or study output folder">
          {activeJobs.map((job) => (
            <div key={job.job_id} className="list-row">
              <div>
                <Link to={`/run?job=${job.job_id}`}>{job.message}</Link>
                <div className="row-meta">
                  Job {job.job_id}
                  {job.experiment_dir ? ` · ${job.experiment_dir}` : ""}
                  {job.study_dir ? ` · ${job.study_dir}` : ""}
                </div>
              </div>
              <span className={`pill ${job.status}`}>{job.status}</span>
            </div>
          ))}
        </SectionCard>
      )}

      <div className="grid grid-2">
        <SectionCard contextLabel="Experiments" title="Recent experiments" subtitle="Each row opens one experiment result folder">
          <table>
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Folder ID</th>
                <th>Domain / Instance</th>
                <th>Runs</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((item) => (
                <tr key={item.id}>
                  <td><Link to={`/experiments/${item.id}`}>{item.name}</Link></td>
                  <td><code className="mono">{item.id}</code></td>
                  <td>{item.domain} / {item.instance}</td>
                  <td>{item.completed_runs}/{item.run_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>

        <SectionCard contextLabel="Studies" title="Scalability studies" subtitle="Each study aggregates multiple instance experiments">
          <table>
            <thead>
              <tr>
                <th>Study</th>
                <th>Folder ID</th>
                <th>Instances</th>
              </tr>
            </thead>
            <tbody>
              {studies.map((item) => (
                <tr key={item.id}>
                  <td><Link to={`/studies/${item.id}`}>{item.name}</Link></td>
                  <td><code className="mono">{item.id}</code></td>
                  <td>{item.instance_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </SectionCard>
      </div>
    </div>
  );
}
