import { ReactNode } from "react";

type Props = {
  kind: "experiment" | "study" | "job" | "dashboard";
  title: string;
  id?: string;
  meta?: string[];
  children?: ReactNode;
};

export function ContextBanner({ kind, title, id, meta = [], children }: Props) {
  return (
    <div className={`context-banner context-${kind}`}>
      <div className="context-banner-main">
        <span className={`context-kind kind-${kind}`}>{kind}</span>
        <div>
          <h1>{title}</h1>
          {id && <div className="context-id">{id}</div>}
          {meta.length > 0 && (
            <div className="context-meta">
              {meta.map((item) => (
                <span key={item} className="context-meta-item">{item}</span>
              ))}
            </div>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

type SectionProps = {
  contextLabel: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function SectionCard({ contextLabel, title, subtitle, children }: SectionProps) {
  return (
    <section className="section-card">
      <div className="section-context">{contextLabel}</div>
      <div className="section-body">
        <h3>{title}</h3>
        {subtitle && <p className="section-subtitle">{subtitle}</p>}
        {children}
      </div>
    </section>
  );
}

type ChartPreviewProps = {
  contextLabel: string;
  title: string;
  src: string;
  alt: string;
};

export function ChartPreview({ contextLabel, title, src, alt }: ChartPreviewProps) {
  return (
    <figure className="chart-figure">
      <figcaption>
        <span className="chart-figure-context">{contextLabel}</span>
        <span className="chart-figure-title">{title}</span>
      </figcaption>
      <img className="chart-preview" src={src} alt={alt} />
    </figure>
  );
}
