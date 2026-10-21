import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from "recharts";
import { getHistory } from "../api";

export default function HistoryModal({ item, districtId, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getHistory(item.item_id, districtId, 30)
      .then((rows) => { if (!cancelled) setData(rows); })
      .catch(() => { if (!cancelled) setError("Could not load history"); });
    return () => { cancelled = true; };
  }, [item.item_id, districtId]);

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="close" onClick={onClose}>X</button>
        <h2>{item.name} - price history</h2>
        <p className="muted">Last 30 days, {"\u20B9"} per {item.unit}</p>

        {error && <p className="error">{error}</p>}
        {!data && !error && <p className="muted">Loading...</p>}
        {data && data.length === 0 && <p className="muted">No history available</p>}

        {data && data.length > 0 && (
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} />
                <YAxis domain={["auto", "auto"]} />
                <Tooltip formatter={(v) => ["\u20B9 " + v, "Price"]} />
                <Line type="monotone" dataKey="price" stroke="#16a34a" strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}