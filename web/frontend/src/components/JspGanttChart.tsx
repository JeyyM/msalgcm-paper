import { useMemo } from "react";
import { SectionCard } from "./ContextBanner";

export type JspOperation = {
  job: number;
  operation_index?: number;
  machine: number;
  processing_time: number;
  start: number;
  finish?: number;
};

type Props = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  operations: JspOperation[];
  makespan: number;
  evaluations?: number;
  knownOptimum?: number;
};

const MACHINE_COLORS = [
  "#2563eb",
  "#059669",
  "#d97706",
  "#dc2626",
  "#7c3aed",
  "#0891b2",
  "#ca8a04",
  "#db2777",
  "#4f46e5",
  "#0d9488",
  "#ea580c",
  "#9333ea",
  "#0284c7",
  "#65a30d",
  "#e11d48",
  "#6366f1",
  "#14b8a6",
  "#f59e0b",
  "#8b5cf6",
  "#06b6d4",
];

const ROW_HEIGHT = 16;
const CHART_LEFT = 72;
const CHART_RIGHT = 16;
const CHART_TOP = 24;
const CHART_BOTTOM = 36;
const MIN_WIDTH = 640;

function machineColor(machine: number): string {
  return MACHINE_COLORS[machine % MACHINE_COLORS.length];
}

export function JspGanttChart({
  contextLabel,
  title,
  subtitle,
  operations,
  makespan,
  evaluations,
  knownOptimum,
}: Props) {
  const layout = useMemo(() => {
    const jobs = [...new Set(operations.map((op) => op.job))].sort((a, b) => a - b);
    const machines = [...new Set(operations.map((op) => op.machine))].sort((a, b) => a - b);
    const span = Math.max(makespan, 1);
    const innerWidth = MIN_WIDTH - CHART_LEFT - CHART_RIGHT;
    const innerHeight = Math.max(jobs.length * ROW_HEIGHT, ROW_HEIGHT);
    const height = innerHeight + CHART_TOP + CHART_BOTTOM;
    const jobIndex = new Map(jobs.map((job, index) => [job, index]));

    const projectX = (time: number) => CHART_LEFT + (time / span) * innerWidth;
    const projectWidth = (duration: number) => Math.max((duration / span) * innerWidth, 1);

    return {
      jobs,
      machines,
      height,
      innerWidth,
      innerHeight,
      jobIndex,
      projectX,
      projectWidth,
      span,
    };
  }, [operations, makespan]);

  const meta =
    subtitle ??
    [
      evaluations != null ? `${evaluations.toLocaleString()} evaluations` : null,
      `Makespan: ${makespan.toFixed(0)}`,
      knownOptimum != null ? `Best known: ${knownOptimum}` : null,
    ]
      .filter(Boolean)
      .join(" · ");

  if (!operations.length) {
    return (
      <SectionCard contextLabel={contextLabel} title={title} subtitle={meta}>
        <div className="chart-box chart-empty">
          <p className="muted">Waiting for schedule data…</p>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={meta}>
      <div className="jsp-gantt-wrap">
        <div className="jsp-gantt-scroll">
          <svg
            viewBox={`0 0 ${MIN_WIDTH} ${layout.height}`}
            className="jsp-gantt-svg"
            role="img"
            aria-label={title}
            preserveAspectRatio="xMinYMin meet"
          >
            {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
              const time = tick * layout.span;
              const x = layout.projectX(time);
              return (
                <g key={`tick-${tick}`}>
                  <line
                    x1={x}
                    y1={CHART_TOP}
                    x2={x}
                    y2={CHART_TOP + layout.innerHeight}
                    className="jsp-gantt-grid"
                  />
                  <text x={x} y={layout.height - 10} textAnchor="middle" className="jsp-gantt-axis-label">
                    {Math.round(time)}
                  </text>
                </g>
              );
            })}

            {layout.jobs.map((job) => {
              const y = CHART_TOP + (layout.jobIndex.get(job) ?? 0) * ROW_HEIGHT + ROW_HEIGHT / 2;
              return (
                <text
                  key={`job-label-${job}`}
                  x={CHART_LEFT - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="jsp-gantt-job-label"
                >
                  J{job}
                </text>
              );
            })}

            {operations.map((operation, index) => {
              const row = layout.jobIndex.get(operation.job) ?? 0;
              const y = CHART_TOP + row * ROW_HEIGHT + 2;
              const x = layout.projectX(operation.start);
              const width = layout.projectWidth(operation.processing_time);
              const barHeight = ROW_HEIGHT - 4;
              return (
                <rect
                  key={`op-${index}-${operation.job}-${operation.start}`}
                  x={x}
                  y={y}
                  width={width}
                  height={barHeight}
                  rx={2}
                  fill={machineColor(operation.machine)}
                  className="jsp-gantt-bar"
                >
                  <title>
                    {`Job ${operation.job}, machine ${operation.machine}, ${operation.processing_time}t @ ${operation.start}`}
                  </title>
                </rect>
              );
            })}
          </svg>
        </div>

        <div className="jsp-gantt-legend">
          {layout.machines.map((machine) => (
            <span key={`machine-${machine}`}>
              <i className="jsp-gantt-swatch" style={{ background: machineColor(machine) }} />
              M{machine}
            </span>
          ))}
        </div>
      </div>
    </SectionCard>
  );
}
