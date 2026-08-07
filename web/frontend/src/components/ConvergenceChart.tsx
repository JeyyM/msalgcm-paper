import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SectionCard } from "./ContextBanner";

type Point = {
  objective_evaluations: number;
  best_objective: number;
  current_objective?: number | null;
};

type Series = {
  name: string;
  data: Point[];
  color: string;
  showCurrent?: boolean;
};

type Props = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  series: Series[];
  embedded?: boolean;
  referenceObjective?: number;
  referenceLabel?: string;
};

function currentSeriesName(name: string) {
  return `${name} (current)`;
}

function computeDomain(values: number[]): [number, number] | undefined {
  if (!values.length) return undefined;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min;
  const pad = span > 0 ? span * 0.08 : Math.max(Math.abs(min) * 0.05, 1);
  return [min - pad, max + pad];
}

export function ConvergenceChart({
  contextLabel,
  title,
  subtitle,
  series,
  embedded = false,
  referenceObjective,
  referenceLabel = "Known optimum",
}: Props) {
  const { data, lineKeys, colors, bestDomain, currentDomain, hasCurrentAxis } = useMemo(() => {
    const merged = new Map<number, Record<string, number>>();
    const keys: { key: string; kind: "best" | "current" }[] = [];
    const palette: Record<string, string> = {};
    const bestValues: number[] = [];
    const currentValues: number[] = [];

    for (const item of series) {
      const showCurrent = item.showCurrent ?? item.data.some((point) => point.current_objective != null);
      palette[item.name] = item.color;
      keys.push({ key: item.name, kind: "best" });

      if (showCurrent) {
        palette[currentSeriesName(item.name)] = item.color;
        keys.push({ key: currentSeriesName(item.name), kind: "current" });
      }

      for (const point of item.data) {
        const row = merged.get(point.objective_evaluations) ?? {
          objective_evaluations: point.objective_evaluations,
        };
        row[item.name] = point.best_objective;
        bestValues.push(point.best_objective);
        if (showCurrent && point.current_objective != null) {
          row[currentSeriesName(item.name)] = point.current_objective;
          currentValues.push(point.current_objective);
        }
        merged.set(point.objective_evaluations, row);
      }
    }

    const rows = Array.from(merged.values()).sort(
      (a, b) => a.objective_evaluations - b.objective_evaluations,
    );

    if (referenceObjective != null) {
      bestValues.push(referenceObjective);
    }

    const showCurrentAxis = currentValues.length > 0;
    return {
      data: rows,
      lineKeys: keys,
      colors: palette,
      bestDomain: computeDomain(bestValues),
      currentDomain: showCurrentAxis ? computeDomain(currentValues) : undefined,
      hasCurrentAxis: showCurrentAxis,
    };
  }, [referenceObjective, series]);

  const chart = data.length ? (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#e5e7eb" />
          <XAxis
            dataKey="objective_evaluations"
            stroke="#6b7280"
            tickFormatter={(value) => Number(value).toLocaleString()}
          />
          <YAxis
            yAxisId="best"
            stroke="#6b7280"
            domain={bestDomain}
            tickFormatter={(value) => Number(value).toFixed(0)}
            label={{ value: "Best objective", angle: -90, position: "insideLeft", fill: "#6b7280", fontSize: 12 }}
          />
          {hasCurrentAxis && (
            <YAxis
              yAxisId="current"
              orientation="right"
              stroke="#94a3b8"
              domain={currentDomain}
              tickFormatter={(value) => Number(value).toFixed(0)}
              label={{ value: "Current objective", angle: 90, position: "insideRight", fill: "#94a3b8", fontSize: 12 }}
            />
          )}
          <Tooltip
            contentStyle={{ background: "#ffffff", border: "1px solid #dbe1ea", color: "#111827" }}
            formatter={(value: number, name: string) => [value.toFixed(1), name]}
            labelFormatter={(label) => `Evaluations: ${Number(label).toLocaleString()}`}
          />
          <Legend />
          {referenceObjective != null && (
            <ReferenceLine
              yAxisId="best"
              y={referenceObjective}
              stroke="#16a34a"
              strokeDasharray="6 4"
              label={{ value: referenceLabel, position: "insideTopRight", fill: "#16a34a", fontSize: 12 }}
            />
          )}
          {lineKeys.map(({ key, kind }) => (
            <Line
              key={key}
              yAxisId={kind === "current" ? "current" : "best"}
              type={kind === "best" ? "stepAfter" : "monotone"}
              dataKey={key}
              stroke={colors[key]}
              strokeOpacity={kind === "current" ? 0.35 : 1}
              strokeWidth={kind === "current" ? 1.2 : 2.5}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  ) : (
    <div className="chart-box chart-empty">
      <p className="muted">Waiting for convergence data…</p>
    </div>
  );

  if (embedded) {
    return chart;
  }

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={subtitle}>
      {chart}
    </SectionCard>
  );
}
