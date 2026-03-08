import { Routes, Route, NavLink } from "react-router-dom";
import DevicesPage from "./pages/DevicesPage";
import TasksPage from "./pages/TasksPage";

export default function App() {
  return (
    <>
      <nav>
        <div className="container">
          <h1>iPhone Device Farm</h1>
          <NavLink to="/">Devices</NavLink>
          <NavLink to="/tasks">Tasks</NavLink>
        </div>
      </nav>
      <div className="container">
        <Routes>
          <Route path="/" element={<DevicesPage />} />
          <Route path="/tasks" element={<TasksPage />} />
        </Routes>
      </div>
    </>
  );
}
