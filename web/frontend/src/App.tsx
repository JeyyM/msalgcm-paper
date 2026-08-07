import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { ResultsDashboardPage } from "./pages/ResultsDashboardPage";
import { DomainPage } from "./pages/DomainPage";
import { FsPage } from "./pages/FsPage";
import { JspPage } from "./pages/JspPage";
import { TspPage } from "./pages/TspPage";
import { ExperimentPage } from "./pages/ExperimentPage";
import { StudyPage } from "./pages/StudyPage";
import { RunPage } from "./pages/RunPage";

function ContextCrumb() {
  const location = useLocation();
  if (location.pathname === "/results") {
    return <span className="nav-context">Results Dashboard</span>;
  }
  if (location.pathname.startsWith("/domains/tsp")) {
    return <span className="nav-context">Travelling Salesman Problem</span>;
  }
  if (location.pathname.startsWith("/domains/scheduling")) {
    return <span className="nav-context">Job Scheduling</span>;
  }
  if (location.pathname.startsWith("/domains/feature-selection")) {
    return <span className="nav-context">Feature Selection</span>;
  }
  if (location.pathname.startsWith("/experiments/")) {
    const id = location.pathname.split("/")[2];
    return <span className="nav-context">Experiment · {id}</span>;
  }
  if (location.pathname.startsWith("/studies/")) {
    const id = location.pathname.split("/")[2];
    return <span className="nav-context">Study · {id}</span>;
  }
  if (location.pathname.startsWith("/run")) {
    return <span className="nav-context">Run monitor</span>;
  }
  return null;
}

export default function App() {
  return (
    <div className="layout">
      <nav className="nav">
        <NavLink to="/" end className="nav-brand">
          MSALGCM
        </NavLink>
        <ContextCrumb />
      </nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/results" element={<ResultsDashboardPage />} />
        <Route path="/domains/tsp" element={<TspPage />} />
        <Route path="/domains/scheduling" element={<JspPage />} />
        <Route path="/domains/feature-selection" element={<FsPage />} />
        <Route path="/domains/:domainId" element={<DomainPage />} />
        <Route path="/experiments/:id" element={<ExperimentPage />} />
        <Route path="/studies/:id" element={<StudyPage />} />
        <Route path="/run" element={<RunPage />} />
      </Routes>
    </div>
  );
}
