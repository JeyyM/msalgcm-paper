import { useMemo } from "react";
import { SectionCard } from "./ContextBanner";

type Coordinate = { x: number; y: number };

type Props = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  route: number[];
  coordinates: Coordinate[];
  distance?: number;
  evaluations?: number;
  knownOptimum?: number;
};

const SVG_SIZE = 420;
const PADDING = 28;

function buildEdges(route: number[], coordinates: Coordinate[]) {
  const nodes = route.map((city, index) => ({
    id: city,
    order: index,
    x: coordinates[city]?.x ?? 0,
    y: coordinates[city]?.y ?? 0,
  }));
  return nodes.map((node, index) => ({
    from: node,
    to: nodes[(index + 1) % nodes.length],
  }));
}

export function TspRouteChart({
  contextLabel,
  title,
  subtitle,
  route,
  coordinates,
  distance,
  evaluations,
  knownOptimum,
}: Props) {
  const layout = useMemo(() => {
    const xs = coordinates.map((point) => point.x);
    const ys = coordinates.map((point) => point.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const spanX = maxX - minX || 1;
    const spanY = maxY - minY || 1;
    const inner = SVG_SIZE - PADDING * 2;

    const project = (x: number, y: number) => ({
      x: PADDING + ((x - minX) / spanX) * inner,
      y: PADDING + (1 - (y - minY) / spanY) * inner,
    });

    return { project };
  }, [coordinates]);

  const edges = useMemo(() => buildEdges(route, coordinates), [route, coordinates]);
  const startCity = route[0] ?? null;

  const meta =
    subtitle ??
    [
      evaluations != null ? `${evaluations.toLocaleString()} evaluations` : null,
      distance != null ? `Tour cost: ${distance.toFixed(1)}` : null,
      knownOptimum != null ? `Optimum: ${knownOptimum}` : null,
    ]
      .filter(Boolean)
      .join(" · ");

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={meta}>
      <div className="tsp-route-wrap">
        <svg viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`} className="tsp-route-svg" role="img" aria-label={title}>
          {edges.map((edge, index) => {
            const from = layout.project(edge.from.x, edge.from.y);
            const to = layout.project(edge.to.x, edge.to.y);
            return (
              <line
                key={`route-${index}`}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                className="tsp-route-edge current"
              />
            );
          })}
          {coordinates.map((point, cityId) => {
            const projected = layout.project(point.x, point.y);
            const isStart = cityId === startCity;
            return (
              <g key={`node-${cityId}`} className={isStart ? "tsp-route-node start" : "tsp-route-node"}>
                <circle cx={projected.x} cy={projected.y} r={isStart ? 6 : 4.5} />
              </g>
            );
          })}
        </svg>
        <div className="tsp-route-legend">
          <span><i className="line current" /> Current tour</span>
          <span><i className="dot start" /> Start city</span>
          <span><i className="dot city" /> City</span>
        </div>
      </div>
    </SectionCard>
  );
}
