import { useEffect, useState } from "react";
import { get, post, type Task } from "../api/client";

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [scriptName, setScriptName] = useState("");
  const [taskName, setTaskName] = useState("");
  const [target, setTarget] = useState("all");
  const [scriptArgs, setScriptArgs] = useState("");

  const fetchTasks = async () => {
    try {
      const data = await get<Task[]>("/api/tasks?limit=50");
      setTasks(data);
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scriptName) return;

    let parsedArgs = null;
    if (scriptArgs.trim()) {
      try {
        parsedArgs = JSON.parse(scriptArgs);
      } catch {
        alert("Invalid JSON in script args");
        return;
      }
    }

    await post("/api/tasks", {
      name: taskName || `Run ${scriptName}`,
      script_name: scriptName,
      script_args: parsedArgs,
      target_devices: target === "all" ? "all" : target.split(",").map((s) => s.trim()),
    });
    setScriptName("");
    setTaskName("");
    setScriptArgs("");
    fetchTasks();
  };

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>Submit Task</h2>
      <form onSubmit={handleSubmit} className="card" style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
        <input
          placeholder="Script name"
          value={scriptName}
          onChange={(e) => setScriptName(e.target.value)}
          style={{ flex: 1, minWidth: 150, padding: 8, borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
        />
        <input
          placeholder="Task name (optional)"
          value={taskName}
          onChange={(e) => setTaskName(e.target.value)}
          style={{ flex: 1, minWidth: 150, padding: 8, borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
        />
        <input
          placeholder="Target: all or UDID"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          style={{ width: 180, padding: 8, borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
        />
        <input
          placeholder='Args JSON (e.g. {"key": "val"})'
          value={scriptArgs}
          onChange={(e) => setScriptArgs(e.target.value)}
          style={{ flex: 1, minWidth: 200, padding: 8, borderRadius: 8, border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
        />
        <button type="submit">Submit</button>
      </form>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>Tasks</h2>
        <button onClick={fetchTasks}>Refresh</button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>ID</th>
              <th style={{ padding: "8px 12px" }}>Name</th>
              <th style={{ padding: "8px 12px" }}>Script</th>
              <th style={{ padding: "8px 12px" }}>Device</th>
              <th style={{ padding: "8px 12px" }}>Status</th>
              <th style={{ padding: "8px 12px" }}>Created</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "8px 12px" }}>{t.id}</td>
                <td style={{ padding: "8px 12px" }}>{t.name}</td>
                <td style={{ padding: "8px 12px", color: "var(--text-dim)" }}>{t.script_name}</td>
                <td style={{ padding: "8px 12px", fontSize: "0.8rem" }}>{t.device_udid?.slice(0, 12) ?? "-"}</td>
                <td style={{ padding: "8px 12px" }}>
                  <span className={`status-badge status-${t.status}`}>{t.status}</span>
                </td>
                <td style={{ padding: "8px 12px", fontSize: "0.8rem", color: "var(--text-dim)" }}>
                  {t.created_at?.slice(0, 19)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
