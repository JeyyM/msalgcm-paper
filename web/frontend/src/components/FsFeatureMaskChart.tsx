import { useMemo } from "react";
import { SectionCard } from "./ContextBanner";

type Props = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  featureMask: number[];
  featureNames?: string[];
  selectedCount?: number;
  totalFeatures?: number;
  cvScore?: number;
  testScore?: number;
  evaluations?: number;
};

function gridColumns(count: number): number {
  if (count <= 30) return 6;
  if (count <= 100) return 10;
  return 12;
}

function featureLabel(names: string[] | undefined, index: number): string {
  const raw = names?.[index] ?? `F${index + 1}`;
  return raw.length <= 5 ? raw : `${raw.slice(0, 4)}…`;
}

export function FsFeatureMaskChart({
  contextLabel,
  title,
  subtitle,
  featureMask,
  featureNames,
  selectedCount,
  totalFeatures,
  cvScore,
  testScore,
  evaluations,
}: Props) {
  const layout = useMemo(() => {
    const total = totalFeatures ?? featureMask.length;
    const selected = selectedCount ?? featureMask.filter((value) => value === 1).length;
    const columns = gridColumns(total);
    return { total, selected, columns };
  }, [featureMask, selectedCount, totalFeatures]);

  const meta =
    subtitle ??
    [
      evaluations != null ? `${evaluations.toLocaleString()} evaluations` : null,
      `${layout.selected}/${layout.total} features selected`,
      cvScore != null ? `CV score ${(cvScore * 100).toFixed(1)}%` : null,
      testScore != null ? `Test score ${(testScore * 100).toFixed(1)}%` : null,
    ]
      .filter(Boolean)
      .join(" · ");

  if (!featureMask.length) {
    return (
      <SectionCard contextLabel={contextLabel} title={title} subtitle={meta}>
        <div className="chart-box chart-empty">
          <p className="muted">Waiting for feature mask…</p>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard contextLabel={contextLabel} title={title} subtitle={meta}>
      <div className="fs-mask-wrap">
        <div
          className="fs-mask-grid"
          style={{ gridTemplateColumns: `repeat(${layout.columns}, minmax(52px, 1fr))` }}
          role="img"
          aria-label={title}
        >
          {featureMask.map((selected, index) => {
            const label = featureLabel(featureNames, index);
            const fullLabel = featureNames?.[index] ?? `F${index + 1}`;
            return (
              <div
                key={`feature-${index}`}
                className={`fs-mask-tile ${selected ? "selected" : "omitted"}`}
                title={`${fullLabel}: ${selected ? "selected" : "omitted"}`}
              >
                <span className="fs-mask-tile-label">{label}</span>
              </div>
            );
          })}
        </div>
        <div className="fs-mask-legend">
          <span><i className="fs-mask-swatch selected" /> Selected</span>
          <span><i className="fs-mask-swatch omitted" /> Omitted</span>
        </div>
      </div>
    </SectionCard>
  );
}
