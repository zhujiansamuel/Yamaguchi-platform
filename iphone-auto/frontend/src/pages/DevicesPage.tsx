import { useEffect, useState } from "react";
import { get, connectWebSocket, type Device } from "../api/client";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDevices = async () => {
    try {
      const data = await get<Device[]>("/api/devices");
      setDevices(data);
    } catch (err) {
      console.error("Failed to fetch devices:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    const ws = connectWebSocket(() => {
      // Refetch on any device event
      fetchDevices();
    });
    return () => ws.close();
  }, []);

  if (loading) return <p>Loading devices...</p>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>Devices ({devices.length})</h2>
        <button onClick={fetchDevices}>Refresh</button>
      </div>

      {devices.length === 0 ? (
        <div className="card">
          <p style={{ color: "var(--text-dim)" }}>No devices found. Connect iPhones via USB.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {devices.map((d) => (
            <div key={d.udid} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <strong>{d.name}</strong>
                <span className={`status-badge status-${d.status}`}>{d.status}</span>
              </div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-dim)" }}>
                {d.model} &middot; iOS {d.ios_version}
              </p>
              <p style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: 4 }}>
                {d.udid}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
