import { Scatter, ScatterChart, ResponsiveContainer, XAxis, YAxis, ZAxis, Line, ComposedChart } from "recharts";

type Props = {
  route: number[];
  coordinates: [number, number][];
  title: string;
};

export function TspRouteChart({ route, coordinates, title }: Props) {
  const points = route.map((city, index) => ({
    x: coordinates[city][0],
    y: coordinates[city][1],
    city,
    order: index,
  }));
  const lines = [...points, points[0]].map((point) => ({ x: point.x, y: point.y }));

  return (
    <div className="card">
      <h3>{title}</h3>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart>
            <XAxis type="number" dataKey="x" stroke="#9ca3af" domain={["auto", "auto"]} />
            <YAxis type="number" dataKey="y" stroke="#9ca3af" domain={["auto", "auto"]} />
            <ZAxis range={[40, 40]} />
            <Line data={lines} dataKey="y" stroke="#60a5fa" dot={false} strokeWidth={1.5} />
            <Scatter data={points} fill="#f87171" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
