import { Link } from "react-router-dom";

const SECTIONS = [
  {
    id: "results",
    title: "Results Dashboard",
    description: "Browse completed experiments, scalability studies, and active jobs.",
    to: "/results",
    accent: "section-accent-neutral",
  },
  {
    id: "tsp",
    title: "Travelling Salesman Problem",
    description: "Compare SA, TS, and PSO on TSPLIB route optimization instances.",
    to: "/domains/tsp",
    accent: "section-accent-tsp",
  },
  {
    id: "scheduling",
    title: "Job Scheduling",
    description: "Classic job-shop scheduling with makespan minimization on Taillard benchmarks.",
    to: "/domains/scheduling",
    accent: "section-accent-scheduling",
  },
  {
    id: "feature-selection",
    title: "Feature Selection",
    description: "Binary feature-subset search with k-NN cross-validation on EW datasets.",
    to: "/domains/feature-selection",
    accent: "section-accent-fs",
  },
] as const;

export function HomePage() {
  return (
    <div className="home-page">
      <header className="home-header">
        <p className="home-eyebrow">MSALGCM Optimization Platform</p>
        <h1>Metaheuristic Comparison</h1>
        <p className="home-lead">
          Simulated Annealing, Tabu Search, and Particle Swarm Optimization across three problem domains.
        </p>
      </header>

      <div className="home-grid">
        {SECTIONS.map((section) => (
          <Link key={section.id} to={section.to} className={`home-card ${section.accent}`}>
            <span className="home-card-label">{section.title}</span>
            <p className="home-card-description">{section.description}</p>
            <span className="home-card-action">Open section →</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
