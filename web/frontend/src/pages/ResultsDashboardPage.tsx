import { Link } from "react-router-dom";
import { Fragment, useEffect, useMemo, useState } from "react";
import {
  ALGO_LABELS,
  api,
  ComparisonDashboard,
  ComparisonDomainBlock,
  ComparisonInstanceRow,
} from "../api";
import { ComparisonGapBarChart, ComparisonGapScalabilityChart, GapChartRow } from "../components/ComparisonGapCharts";
import { ContextBanner, SectionCard } from "../components/ContextBanner";

const ALGO_IDS = ["simulated_annealing", "tabu_search", "particle_swarm"] as const;

function fmtNum(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

function fmtGap(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(2)}%`;
}

function statusBadge(result: ComparisonInstanceRow["results"][string] | undefined) {
  if (!result || result.completed_runs === 0) {
    return <span className="pill pending">Not started</span>;
  }
  if (result.done) {
    return <span className="pill completed">30/30</span>;
  }
  return (
    <span className="pill running">
      {result.completed_runs}/{result.target_runs}
    </span>
  );
}

function bestGapWinner(row: ComparisonInstanceRow): string | null {
  let winner: string | null = null;
  let best = Infinity;
  for (const alg of ALGO_IDS) {
    const gap = row.results[alg]?.best_gap_percentage;
    if (gap != null && gap < best) {
      best = gap;
      winner = alg;
    }
  }
  return winner;
}

function toBarChartData(domain: ComparisonDomainBlock): GapChartRow[] {
  return domain.instances
    .map((row) => {
      const point: GapChartRow = { instance: row.instance };
      let hasGap = false;
      for (const alg of ALGO_IDS) {
        const gap = row.results[alg]?.best_gap_percentage;
        if (gap != null) {
          point[alg] = gap;
          hasGap = true;
        }
      }
      return hasGap ? point : null;
    })
    .filter((row): row is GapChartRow => row != null);
}

function toScalabilityData(domain: ComparisonDomainBlock) {
  return domain.instances
    .filter((row) => row.problem_size != null)
    .sort((a, b) => (a.problem_size ?? 0) - (b.problem_size ?? 0))
    .map((row) => {
      const point: {
        problem_size: number;
        label: string;
        simulated_annealing?: number;
        tabu_search?: number;
        particle_swarm?: number;
      } = {
        problem_size: row.problem_size!,
        label: row.problem_size_label || row.instance,
      };
      for (const alg of ALGO_IDS) {
        const gap = row.results[alg]?.best_gap_percentage;
        if (gap != null) point[alg] = gap;
      }
      return point;
    })
    .filter((row) => ALGO_IDS.some((alg) => row[alg] != null));
}

function domainSynthesis(domain: ComparisonDomainBlock) {
  const wins: Record<string, number> = Object.fromEntries(ALGO_IDS.map((a) => [a, 0]));
  const gaps: Record<string, number[]> = Object.fromEntries(ALGO_IDS.map((a) => [a, []]));
  const runtimes: Record<string, number[]> = Object.fromEntries(ALGO_IDS.map((a) => [a, []]));

  for (const row of domain.instances) {
    const winner = bestGapWinner(row);
    if (winner) wins[winner] += 1;
    for (const alg of ALGO_IDS) {
      const result = row.results[alg];
      if (result?.done && result.best_gap_percentage != null) {
        gaps[alg].push(result.best_gap_percentage);
      }
      if (result?.completed_runs && result.mean_runtime_seconds != null) {
        runtimes[alg].push(result.mean_runtime_seconds);
      }
    }
  }

  const meanGap = (alg: string) => {
    const values = gaps[alg];
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  };

  const meanRuntime = (alg: string) => {
    const values = runtimes[alg];
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  };

  return { wins, meanGap, meanRuntime };
}

function DomainSection({ domain }: { domain: ComparisonDomainBlock }) {
  const barData = useMemo(() => toBarChartData(domain), [domain]);
  const scaleData = useMemo(() => toScalabilityData(domain), [domain]);
  const synthesis = useMemo(() => domainSynthesis(domain), [domain]);
  const sizeLabel = domain.id === "tsp" ? "Cities" : "Jobs × machines";

  return (
    <div className={`domain-results-block domain-results-${domain.id}`}>
      <header className="domain-results-header">
        <h2>{domain.label}</h2>
        <p className="domain-results-meta">
          {domain.objective} · {domain.evaluation_budget.toLocaleString()} eval budget · {domain.target_runs} runs
          per algorithm
        </p>
      </header>

      <SectionCard
        contextLabel=""
        title="Synthesis"
        subtitle="Gap to known optimum / BKS · lower is better"
      >
        <div className="synthesis-grid">
          {ALGO_IDS.map((alg) => (
            <div key={alg} className="synthesis-card">
              <span className="synthesis-card-title">{ALGO_LABELS[alg]}</span>
              <span className="synthesis-stat">{synthesis.wins[alg]} instance wins</span>
              <span className="synthesis-meta">
                avg best gap {fmtGap(synthesis.meanGap(alg))} · avg runtime{" "}
                {synthesis.meanRuntime(alg) != null ? `${synthesis.meanRuntime(alg)!.toFixed(1)}s` : "—"}
              </span>
            </div>
          ))}
        </div>
      </SectionCard>

      <div className="grid grid-2">
        <ComparisonGapBarChart
          contextLabel=""
          title="Best gap by instance"
          subtitle="Best of 30 seeds vs known optimum / BKS"
          data={barData}
        />
        <ComparisonGapScalabilityChart
          contextLabel=""
          title="Gap vs problem size"
          subtitle="Trend across instance scale (complete runs only in averages)"
          data={scaleData}
          sizeLabel={sizeLabel}
        />
      </div>

      <SectionCard
        contextLabel=""
        title="Full comparison table"
        subtitle={`${domain.evaluation_budget.toLocaleString()} eval budget · ${domain.target_runs} runs per algorithm`}
      >
        <div className="comparison-table-wrap">
          <table className="comparison-table">
            <thead>
              <tr>
                <th rowSpan={2}>Instance</th>
                <th rowSpan={2}>Size</th>
                <th rowSpan={2}>{domain.instances[0]?.optimum_label ?? "Optimum"}</th>
                {ALGO_IDS.map((alg) => (
                  <th key={alg} colSpan={4}>
                    {ALGO_LABELS[alg]}
                  </th>
                ))}
              </tr>
              <tr className="comparison-subhead">
                {ALGO_IDS.flatMap((alg) => [
                  <th key={`${alg}-best`}>Best</th>,
                  <th key={`${alg}-gap`}>Gap</th>,
                  <th key={`${alg}-rt`}>Runtime</th>,
                  <th key={`${alg}-status`}>Status</th>,
                ])}
              </tr>
            </thead>
            <tbody>
              {domain.instances.map((row) => {
                const winner = bestGapWinner(row);
                return (
                  <tr key={row.instance}>
                    <td>
                      <strong>{row.instance}</strong>
                    </td>
                    <td>{row.problem_size_label}</td>
                    <td>{row.known_optimum != null ? fmtNum(row.known_optimum, 0) : "—"}</td>
                    {ALGO_IDS.map((alg) => {
                      const result = row.results[alg];
                      const isWinner = winner === alg && result?.best_gap_percentage != null;
                      return (
                        <Fragment key={`${row.instance}-${alg}`}>
                          <td className={isWinner ? "cell-best" : undefined}>
                            {result?.best_objective != null ? fmtNum(result.best_objective, 0) : "—"}
                          </td>
                          <td className={isWinner ? "cell-best" : undefined}>
                            {fmtGap(result?.best_gap_percentage)}
                            {result?.mean_gap_percentage != null && (
                              <div className="row-meta">μ {fmtGap(result.mean_gap_percentage)}</div>
                            )}
                          </td>
                          <td>
                            {result?.mean_runtime_seconds != null
                              ? `${result.mean_runtime_seconds.toFixed(1)}s`
                              : "—"}
                          </td>
                          <td>
                            {statusBadge(result)}
                            {result?.experiment_id && (
                              <div className="row-meta">
                                <Link to={`/experiments/${result.experiment_id}`}>open</Link>
                              </div>
                            )}
                          </td>
                        </Fragment>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}

function CrossDomainSummary({ comparison }: { comparison: ComparisonDashboard }) {
  const rows = useMemo(() => {
    return ALGO_IDS.map((alg) => {
      let totalWins = 0;
      const gaps: number[] = [];
      for (const domain of comparison.domains) {
        const syn = domainSynthesis(domain);
        totalWins += syn.wins[alg];
        const mg = syn.meanGap(alg);
        if (mg != null) gaps.push(mg);
      }
      return {
        alg,
        label: ALGO_LABELS[alg],
        wins: totalWins,
        avgGap: gaps.length ? gaps.reduce((a, b) => a + b, 0) / gaps.length : null,
      };
    }).sort((a, b) => (a.avgGap ?? Infinity) - (b.avgGap ?? Infinity));
  }, [comparison]);

  const leader = rows[0];

  return (
    <SectionCard
      contextLabel="Cross-domain"
      title="Overall ranking (TSP + JSP)"
      subtitle="Instance-win counts and mean best-gap across complete comparison runs"
    >
      <table className="comparison-table synthesis-summary-table">
        <thead>
          <tr>
            <th>Algorithm</th>
            <th>Instance wins</th>
            <th>Mean best gap (complete runs)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.alg} className={index === 0 ? "row-leader" : undefined}>
              <td>
                <strong>{row.label}</strong>
                {index === 0 && row.avgGap != null && <span className="pill completed">lowest avg gap</span>}
              </td>
              <td>{row.wins}</td>
              <td>{fmtGap(row.avgGap)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {leader?.avgGap != null && (
        <p className="synthesis-lead muted">
          <strong>{leader.label}</strong> leads on average gap across domains with complete data. PSO shows large
          TSP gaps on permutations; JSP results are mixed while several batches are still in progress.
        </p>
      )}
    </SectionCard>
  );
}

export function ResultsDashboardPage() {
  const [comparison, setComparison] = useState<ComparisonDashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .comparisonDashboard()
      .then((data) => {
        setComparison(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message || "Failed to load comparison dashboard"))
      .finally(() => setLoading(false));
  }, []);

  const completionSummary = useMemo(() => {
    if (!comparison) return null;
    let complete = 0;
    let partial = 0;
    let missing = 0;
    for (const domain of comparison.domains) {
      for (const row of domain.instances) {
        for (const alg of ALGO_IDS) {
          const result = row.results[alg];
          if (!result || result.completed_runs === 0) missing += 1;
          else if (result.done) complete += 1;
          else partial += 1;
        }
      }
    }
    return { complete, partial, missing };
  }, [comparison]);

  return (
    <div>
      <ContextBanner
        kind="dashboard"
        title="Results Dashboard"
        meta={["Final comparison", "TSP + JSP", "Gap vs known optimum / BKS"]}
      />

      {comparison && !comparison.feature_selection_included && (
        <p className="dashboard-note muted">{comparison.feature_selection_note}</p>
      )}

      {loading && <p className="muted">Loading comparison data…</p>}

      {error && (
        <SectionCard contextLabel="Error" title="Could not load results" subtitle="Restart npm run dev if you recently updated the API">
          <p className="status-pending">{error}</p>
        </SectionCard>
      )}

      {completionSummary && (
        <SectionCard contextLabel="Overview" title="Completion snapshot" subtitle="Comparison cells (instance × algorithm)">
          <div className="completion-stats">
            <span className="pill completed">{completionSummary.complete} complete (30/30)</span>
            <span className="pill running">{completionSummary.partial} in progress</span>
            <span className="pill pending">{completionSummary.missing} not started</span>
          </div>
        </SectionCard>
      )}

      {comparison && (
        <>
          <CrossDomainSummary comparison={comparison} />
          {comparison.domains.map((domain) => (
            <DomainSection key={domain.id} domain={domain} />
          ))}
        </>
      )}
    </div>
  );
}
