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
import { ALGO_LABELS } from "../api";
import { SectionCard } from "./ContextBanner";

type Row = {
  problem_size: string;
  algorithm: string;
  instance?: string;
  best_gap_percentage?: string;
  mean_gap_percentage?: string;
};

type Props = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  rows: Row[];
  metric: "best_gap_percentage" | "mean_gap_percentage";
};

const COLORS = ["#2563eb", "#059669", "#d97706"];

export function ScalabilityChart({ contextLabel, title, subtitle, rows, metric }: Props) {
  const algorithms = Array.from(new Set(rows.map((row) => row.algorithm))).sort();
  const sizes = Array.from(new Set(rows.map((row) => Number(row.problem_size)))).sort((a, b) => a - b);

  const data = sizes.map((size) => {
    const point: Record<string, number | string> = { problem_size: size };
    for (const algorithm of algorithms) {
      const row = rows.find((item) => item.algorithm === algorithm && Number(item.problem_size) === size);
      if (row && row[metric]) {
        point[ALGO_LABELS[algorithm] ?? algorithm] = Number(row[metric]);
      }
    }
    return point;
  });

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={subtitle}>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#e5e7eb" />
            <XAxis dataKey="problem_size" stroke="#6b7280" label={{ value: "Cities", position: "insideBottom", offset: -5 }} />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ background: "#ffffff", border: "1px solid #dbe1ea", color: "#111827" }} />
            <Legend />
            {algorithms.map((algorithm, index) => (
              <Line
                key={algorithm}
                type="monotone"
                dataKey={ALGO_LABELS[algorithm] ?? algorithm}
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={2}
                dot
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}
