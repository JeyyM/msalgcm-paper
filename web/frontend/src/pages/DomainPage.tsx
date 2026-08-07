import { Link, useNavigate, useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { api, ExperimentSummary } from "../api";
import { ContextBanner, SectionCard } from "../components/ContextBanner";

type DomainKey = "tsp" | "scheduling" | "feature-selection";

const DOMAIN_META: Record<
  DomainKey,
  { title: string; domain: string; description: string; accent: string }
> = {
  tsp: {
    title: "Travelling Salesman Problem",
    domain: "tsp",
    description: "Route optimization on TSPLIB instances. Objective: minimize total tour distance.",
    accent: "section-accent-tsp",
  },
  scheduling: {
    title: "Job Scheduling",
    domain: "scheduling",
    description: "Classic job-shop scheduling on Taillard benchmarks. Objective: minimize makespan.",
    accent: "section-accent-scheduling",
  },
  "feature-selection": {
    title: "Feature Selection",
    domain: "feature_selection",
    description: "Binary feature-subset search on EW datasets with k-NN cross-validation.",
    accent: "section-accent-fs",
  },
};

function isDomainKey(value: string | undefined): value is DomainKey {
  return value === "tsp" || value === "scheduling" || value === "feature-selection";
}

export function DomainPage() {
  const { domainId } = useParams<{ domainId: string }>();
  const navigate = useNavigate();
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [configs, setConfigs] = useState<any[]>([]);
  const [selectedConfig, setSelectedConfig] = useState("");
  const [starting, setStarting] = useState(false);

  const meta = isDomainKey(domainId) ? DOMAIN_META[domainId] : null;

  useEffect(() => {
    if (!meta) return;
    api.dashboard().then((data) => {
      setExperiments(data.experiments.filter((item) => item.domain === meta.domain));
    });
    api.listConfigs().then((items) => {
      const filtered = items.filter(
        (item) => item.kind === "experiment" && item.domain === meta.domain,
      );
      setConfigs(filtered);
      if (filtered.length) {
        setSelectedConfig(filtered[0].path);
      }
    });
  }, [meta]);

  const selected = useMemo(
    () => configs.find((item) => item.path === selectedConfig),
    [configs, selectedConfig],
  );

  async function startRun() {
    if (!selectedConfig) return;
    setStarting(true);
    try {
      const result = await api.startJob(selectedConfig, "experiment");
      navigate(`/run?job=${result.job_id}`);
    } finally {
      setStarting(false);
    }
  }

  if (!meta) {
    return <p>Unknown domain.</p>;
  }

  return (
    <div>
      <ContextBanner
        kind="dashboard"
        title={meta.title}
        meta={[meta.domain, "SA · TS · PSO"]}
      />

      <SectionCard
        contextLabel={meta.title}
        title="About this domain"
        subtitle="All three metaheuristics share the same evaluation budget and logging"
      >
        <p className="domain-description">{meta.description}</p>
      </SectionCard>

      <SectionCard
        contextLabel={`${meta.title} · Launch`}
        title="Run an experiment"
        subtitle="Select a prepared config and start a new timestamped results folder"
      >
        <div className="launch-row">
          <select
            value={selectedConfig}
            onChange={(event) => setSelectedConfig(event.target.value)}
            className="wide-select"
            disabled={!configs.length}
          >
            {configs.map((item) => (
              <option key={item.path} value={item.path}>
                {item.name} · {item.instance}
              </option>
            ))}
          </select>
          <button onClick={startRun} disabled={!selectedConfig || starting}>
            {starting ? "Starting…" : `Run ${selected?.name ?? "experiment"}`}
          </button>
          <Link className="button-link secondary" to={`/run?domain=${domainId}`}>
            Advanced launch
          </Link>
        </div>
        {!configs.length && <p className="muted">No example configs found for this domain yet.</p>}
      </SectionCard>

      <SectionCard
        contextLabel={`${meta.title} · Results`}
        title="Recent experiments"
        subtitle="Experiments in this domain only"
      >
        {experiments.length === 0 ? (
          <p className="muted">No completed experiments for {meta.title} yet.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Experiment</th>
                <th>Instance</th>
                <th>Folder ID</th>
                <th>Runs</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((item) => (
                <tr key={item.id}>
                  <td><Link to={`/experiments/${item.id}`}>{item.name}</Link></td>
                  <td>{item.instance}</td>
                  <td><code className="mono">{item.id}</code></td>
                  <td>{item.completed_runs}/{item.run_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </SectionCard>
    </div>
  );
}
