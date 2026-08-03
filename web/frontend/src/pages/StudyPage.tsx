import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ALGO_LABELS, api } from "../api";
import { ChartPreview, ContextBanner, SectionCard } from "../components/ContextBanner";
import { ScalabilityChart } from "../components/ScalabilityChart";
import { formatStudyContext } from "../utils/labels";

export function StudyPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [selectedInstance, setSelectedInstance] = useState<string>("all");

  useEffect(() => {
    if (!id) return;
    api.getStudy(id).then(setData);
  }, [id]);

  const ctx = useMemo(
    () => (data ? formatStudyContext({ id: data.id, name: data.name, instance_count: data.manifest.experiments.length }) : null),
    [data],
  );

  const instances = useMemo((): string[] => {
    if (!data?.scalability_summary) return [];
    const names = (data.scalability_summary as { instance: string }[]).map((row) => row.instance);
    return [...new Set(names)].sort();
  }, [data]);

  const filteredRows = useMemo(() => {
    if (!data) return [];
    if (selectedInstance === "all") return data.scalability_summary;
    return data.scalability_summary.filter((row: any) => row.instance === selectedInstance);
  }, [data, selectedInstance]);

  if (!data || !ctx) return <p>Loading study...</p>;

  return (
    <div>
      <ContextBanner
        kind="study"
        title={ctx.name}
        id={ctx.id}
        meta={[`${data.manifest.experiments.length} instances`, "Scalability comparison"]}
      />

      <SectionCard
        contextLabel={ctx.fullLabel}
        title="Included experiments"
        subtitle="Each instance maps to one experiment result folder"
      >
        <table>
          <thead>
            <tr>
              <th>Instance</th>
              <th>Size</th>
              <th>Experiment folder</th>
              <th>Open</th>
            </tr>
          </thead>
          <tbody>
            {data.manifest.experiments.map((item: any) => (
              <tr key={item.instance}>
                <td>{item.instance}</td>
                <td>{item.problem_size}</td>
                <td><code className="mono">{item.experiment_dir}</code></td>
                <td><Link to={`/experiments/${item.experiment_dir}`}>View experiment</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      <SectionCard
        contextLabel={ctx.fullLabel}
        title="Chart filter"
        subtitle="Scope scalability charts to one instance or all instances in this study"
      >
        <select value={selectedInstance} onChange={(event) => setSelectedInstance(event.target.value)}>
          <option value="all">All instances in {ctx.name}</option>
          {instances.map((instance) => (
            <option key={instance} value={instance}>{instance}</option>
          ))}
        </select>
      </SectionCard>

      <ScalabilityChart
        contextLabel={`${ctx.fullLabel}${selectedInstance !== "all" ? ` · ${selectedInstance}` : ""}`}
        title="Best gap from optimum vs problem size"
        subtitle={`Study: ${ctx.name}${selectedInstance !== "all" ? ` · Instance: ${selectedInstance}` : ""}`}
        rows={filteredRows}
        metric="best_gap_percentage"
      />
      <ScalabilityChart
        contextLabel={`${ctx.fullLabel}${selectedInstance !== "all" ? ` · ${selectedInstance}` : ""}`}
        title="Mean gap from optimum vs problem size"
        subtitle={`Study: ${ctx.name}${selectedInstance !== "all" ? ` · Instance: ${selectedInstance}` : ""}`}
        rows={filteredRows}
        metric="mean_gap_percentage"
      />

      <SectionCard
        contextLabel={ctx.fullLabel}
        title="Scalability summary"
        subtitle="Each row is one algorithm on one instance within this study"
      >
        <table>
          <thead>
            <tr>
              <th>Instance</th>
              <th>Size</th>
              <th>Algorithm</th>
              <th>Experiment folder</th>
              <th>Best</th>
              <th>Gap %</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row: any) => (
              <tr key={`${row.instance}-${row.algorithm}`}>
                <td>{row.instance}</td>
                <td>{row.problem_size}</td>
                <td>{ALGO_LABELS[row.algorithm] ?? row.algorithm}</td>
                <td><Link to={`/experiments/${row.experiment_dir}`}><code className="mono">{row.experiment_dir}</code></Link></td>
                <td>{Number(row.min_objective).toFixed(1)}</td>
                <td>{row.best_gap_percentage ? Number(row.best_gap_percentage).toFixed(1) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      {data.charts?.length > 0 && (
        <SectionCard
          contextLabel={ctx.fullLabel}
          title="Study charts"
          subtitle="PNG exports generated for this study folder"
        >
          <div className="grid grid-2">
            {data.charts.map((chart: string) => (
              <ChartPreview
                key={chart}
                contextLabel={ctx.fullLabel}
                title={chart}
                src={api.studyChartUrl(data.id, chart)}
                alt={`${ctx.name} ${chart}`}
              />
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
