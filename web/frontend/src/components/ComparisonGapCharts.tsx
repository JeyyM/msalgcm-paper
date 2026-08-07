import {
  Bar,
  BarChart,
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

const ALGO_COLORS: Record<string, string> = {
  simulated_annealing: "#2563eb",
  tabu_search: "#059669",
  particle_swarm: "#d97706",
};

export type GapChartRow = {
  instance: string;
  simulated_annealing?: number;
  tabu_search?: number;
  particle_swarm?: number;
};

type GapBarChartProps = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  data: GapChartRow[];
};

export function ComparisonGapBarChart({ contextLabel, title, subtitle, data }: GapBarChartProps) {
  if (!data.length) {
    return (
      <SectionCard contextLabel={contextLabel} title={title} subtitle={subtitle}>
        <div className="chart-box chart-empty">
          <p className="muted">No completed runs with gap data yet.</p>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={subtitle}>
      <div className="chart-box chart-box-tall">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
            <CartesianGrid stroke="#e5e7eb" vertical={false} />
            <XAxis dataKey="instance" stroke="#6b7280" tick={{ fontSize: 12 }} />
            <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} unit="%" label={{ value: "Gap %", angle: -90, position: "insideLeft" }} />
            <Tooltip
              formatter={(value: number) => [`${value.toFixed(2)}%`, "Gap"]}
              contentStyle={{ background: "#ffffff", border: "1px solid #dbe1ea", color: "#111827" }}
            />
            <Legend />
            <Bar dataKey="simulated_annealing" name={ALGO_LABELS.simulated_annealing} fill={ALGO_COLORS.simulated_annealing} radius={[4, 4, 0, 0]} />
            <Bar dataKey="tabu_search" name={ALGO_LABELS.tabu_search} fill={ALGO_COLORS.tabu_search} radius={[4, 4, 0, 0]} />
            <Bar dataKey="particle_swarm" name={ALGO_LABELS.particle_swarm} fill={ALGO_COLORS.particle_swarm} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}

type ScalabilityRow = {
  problem_size: number;
  label: string;
  simulated_annealing?: number;
  tabu_search?: number;
  particle_swarm?: number;
};

type GapScalabilityChartProps = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  data: ScalabilityRow[];
  sizeLabel: string;
};

export function ComparisonGapScalabilityChart({
  contextLabel,
  title,
  subtitle,
  data,
  sizeLabel,
}: GapScalabilityChartProps) {
  if (!data.length) return null;

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={subtitle}>
      <div className="chart-box chart-box-tall">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
            <CartesianGrid stroke="#e5e7eb" />
            <XAxis dataKey="label" stroke="#6b7280" tick={{ fontSize: 11 }} label={{ value: sizeLabel, position: "insideBottom", offset: -5 }} />
            <YAxis stroke="#6b7280" unit="%" />
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} contentStyle={{ background: "#fff", border: "1px solid #dbe1ea" }} />
            <Legend />
            <Line type="monotone" dataKey="simulated_annealing" name={ALGO_LABELS.simulated_annealing} stroke={ALGO_COLORS.simulated_annealing} strokeWidth={2} dot />
            <Line type="monotone" dataKey="tabu_search" name={ALGO_LABELS.tabu_search} stroke={ALGO_COLORS.tabu_search} strokeWidth={2} dot />
            <Line type="monotone" dataKey="particle_swarm" name={ALGO_LABELS.particle_swarm} stroke={ALGO_COLORS.particle_swarm} strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}
