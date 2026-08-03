import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { DashboardPage } from "./pages/DashboardPage";
import { ExperimentPage } from "./pages/ExperimentPage";
import { StudyPage } from "./pages/StudyPage";
import { RunPage } from "./pages/RunPage";

function ContextCrumb() {
  const location = useLocation();
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
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/run">Run Experiment</NavLink>
        <ContextCrumb />
      </nav>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/experiments/:id" element={<ExperimentPage />} />
        <Route path="/studies/:id" element={<StudyPage />} />
        <Route path="/run" element={<RunPage />} />
      </Routes>
    </div>
  );
}
