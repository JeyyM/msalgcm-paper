import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SectionCard } from "./ContextBanner";

type Point = {
  objective_evaluations: number;
  best_objective: number;
};

type Props = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  series: { name: string; data: Point[]; color: string }[];
  embedded?: boolean;
};

export function ConvergenceChart({ contextLabel, title, subtitle, series, embedded = false }: Props) {
  const merged = new Map<number, Record<string, number>>();
  for (const item of series) {
    for (const point of item.data) {
      const row = merged.get(point.objective_evaluations) ?? { objective_evaluations: point.objective_evaluations };
      row[item.name] = point.best_objective;
      merged.set(point.objective_evaluations, row);
    }
  }
  const data = Array.from(merged.values()).sort(
    (a, b) => a.objective_evaluations - b.objective_evaluations,
  );

  const chart = (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#1f2937" />
          <XAxis dataKey="objective_evaluations" stroke="#9ca3af" />
          <YAxis stroke="#9ca3af" />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
          <Legend />
          {series.map((item) => (
            <Line
              key={item.name}
              type="monotone"
              dataKey={item.name}
              stroke={item.color}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
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
