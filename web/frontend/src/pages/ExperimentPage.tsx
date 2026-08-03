import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ALGO_LABELS, api } from "../api";
import { ChartPreview, ContextBanner, SectionCard } from "../components/ContextBanner";
import { ConvergenceChart } from "../components/ConvergenceChart";
import { formatExperimentContext } from "../utils/labels";

const COLORS = ["#60a5fa", "#34d399", "#fbbf24"];

export function ExperimentPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [selectedRun, setSelectedRun] = useState<string>("");
  const [convergence, setConvergence] = useState<any[]>([]);
  const [multiSeries, setMultiSeries] = useState<any[]>([]);

  const ctx = useMemo(
    () => (data ? formatExperimentContext(data) : null),
    [data],
  );

  useEffect(() => {
    if (!id) return;
    api.getExperiment(id).then(setData);
  }, [id]);

  useEffect(() => {
    if (data?.runs?.length && !selectedRun) {
      setSelectedRun(data.runs[0].run_id);
    }
  }, [data, selectedRun]);

  useEffect(() => {
    if (!id || !selectedRun) return;
    api.getConvergence(id, selectedRun).then(setConvergence);
  }, [id, selectedRun]);

  useEffect(() => {
    if (!id || !data) return;
    const algorithms = Array.from(new Set(data.runs.map((run: any) => run.algorithm as string)));
    Promise.all(
      algorithms.map(async (algorithm, index) => {
        const run = data.runs
          .filter((item: any) => item.algorithm === algorithm)
          .sort((a: any, b: any) => Number(a.best_objective) - Number(b.best_objective))[0];
        const points = await api.getConvergence(id, run.run_id);
        return {
          name: `${ALGO_LABELS[algorithm as string] ?? algorithm} (${run.run_id})`,
          data: points,
          color: COLORS[index % COLORS.length],
        };
      }),
    ).then(setMultiSeries);
  }, [id, data]);

  const runs = data?.runs ?? [];
  const selectedRunRow = runs.find((run: any) => run.run_id === selectedRun);

  if (!data || !ctx) return <p>Loading experiment...</p>;

  return (
    <div>
      <ContextBanner
        kind="experiment"
        title={ctx.name}
        id={ctx.id}
        meta={[
          ctx.scope ?? "",
          `${data.run_count} runs`,
          `${data.completed_runs} completed`,
        ].filter(Boolean)}
      />

      <SectionCard
        contextLabel={ctx.fullLabel}
        title="Algorithm summary"
        subtitle="Aggregated metrics for this experiment only"
      >
        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Mean</th>
              <th>Best</th>
              <th>Gap %</th>
              <th>Runtime (s)</th>
            </tr>
          </thead>
          <tbody>
            {data.summary.map((row: any) => (
              <tr key={row.algorithm}>
                <td>{ALGO_LABELS[row.algorithm] ?? row.algorithm}</td>
                <td>{Number(row.mean_objective).toFixed(1)}</td>
                <td>{Number(row.min_objective).toFixed(1)}</td>
                <td>{row.best_gap_percentage ? Number(row.best_gap_percentage).toFixed(1) : "—"}</td>
                <td>{Number(row.mean_runtime_seconds).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      <SectionCard
        contextLabel={ctx.fullLabel}
        title="All runs"
        subtitle="Every run belongs to this experiment folder"
      >
        <table>
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Algorithm</th>
              <th>Seed</th>
              <th>Best</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run: any) => (
              <tr key={run.run_id} className={run.run_id === selectedRun ? "row-selected" : ""}>
                <td>
                  <button className="linkish" onClick={() => setSelectedRun(run.run_id)}>
                    {run.run_id}
                  </button>
                </td>
                <td>{ALGO_LABELS[run.algorithm] ?? run.algorithm}</td>
                <td>{run.seed}</td>
                <td>{Number(run.best_objective).toFixed(1)}</td>
                <td>{run.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      {multiSeries.length > 0 && (
        <ConvergenceChart
          contextLabel={ctx.fullLabel}
          title="Best run convergence by algorithm"
          subtitle={`Best-performing run per algorithm within ${ctx.name}`}
          series={multiSeries}
        />
      )}

      <SectionCard
        contextLabel={`${ctx.fullLabel} · ${selectedRun}`}
        title="Single run convergence"
        subtitle={selectedRunRow ? `${selectedRunRow.algorithm} · seed ${selectedRunRow.seed}` : undefined}
      >
        <select value={selectedRun} onChange={(event) => setSelectedRun(event.target.value)}>
          {runs.map((run: any) => (
            <option key={run.run_id} value={run.run_id}>
              {run.run_id} · {ALGO_LABELS[run.algorithm] ?? run.algorithm} · best={Number(run.best_objective).toFixed(1)}
            </option>
          ))}
        </select>
        {convergence.length > 0 && (
          <ConvergenceChart
            embedded
            contextLabel={`${ctx.fullLabel} · ${selectedRun}`}
            title={`Convergence for ${selectedRun}`}
            subtitle={`Experiment: ${ctx.name}`}
            series={[{ name: selectedRun, data: convergence, color: "#60a5fa" }]}
          />
        )}
      </SectionCard>

      {data.charts?.length > 0 && (
        <SectionCard
          contextLabel={ctx.fullLabel}
          title="Generated charts"
          subtitle="Static PNG exports saved for this experiment"
        >
          <div className="grid grid-2">
            {data.charts.map((chart: string) => (
              <ChartPreview
                key={chart}
                contextLabel={ctx.fullLabel}
                title={chart}
                src={api.chartUrl(data.id, chart)}
                alt={`${ctx.name} ${chart}`}
              />
            ))}
          </div>
        </SectionCard>
      )}
    </div>
  );
}
