import { useEffect, useState } from "react";
import { getStates, getDistricts, getPrices } from "./api";
import PriceCard from "./components/PriceCard.jsx";
import HistoryModal from "./components/HistoryModal.jsx";

const CATEGORIES = [
  { key: "all", label: "All" },
  { key: "vegetable", label: "Vegetables" },
  { key: "fruit", label: "Fruits" },
  { key: "grocery", label: "Groceries" },
];

export default function App() {
  const [states, setStates] = useState([]);
  const [stateId, setStateId] = useState("");
  const [districts, setDistricts] = useState([]);
  const [districtId, setDistrictId] = useState("");
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [data, setData] = useState({ latest_date: null, items: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  // 1. load states once
  useEffect(() => {
    getStates()
      .then((list) => {
        setStates(list);
        if (list.length > 0) {
          const ap = list.find((s) => s.name === "Andhra Pradesh");
          setStateId(String((ap || list[0]).id));
        }
      })
      .catch(() => setError("Cannot connect to the server. Is the backend running?"));
  }, []);

  // 2. load districts when state changes
  useEffect(() => {
    if (!stateId) return;
    setDistricts([]);
    setDistrictId("");
    getDistricts(stateId)
      .then((list) => {
        setDistricts(list);
        if (list.length > 0) setDistrictId(String(list[0].id));
      })
      .catch(() => setError("Could not load districts"));
  }, [stateId]);

  // 3. load prices when district / category / search changes (+ auto refresh every 5 min)
  useEffect(() => {
    if (!districtId) return;
    let cancelled = false;

    const load = () => {
      setLoading(true);
      getPrices(districtId, category, search.trim())
        .then((res) => {
          if (!cancelled) {
            setData(res);
            setError("");
          }
        })
        .catch(() => { if (!cancelled) setError("Could not load prices"); })
        .finally(() => { if (!cancelled) setLoading(false); });
    };

    const timer = setTimeout(load, 300);
    const refresh = setInterval(load, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearTimeout(timer);
      clearInterval(refresh);
    };
  }, [districtId, category, search]);

  return (
    <div className="app">
      <header className="hero">
        <h1>Gouraw Grocery Price Tracker</h1>
        <p>Daily vegetable, fruit and grocery prices - state and district wise</p>
      </header>

      <section className="filters">
        <select value={stateId} onChange={(e) => setStateId(e.target.value)}>
          {states.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        <select value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
          {districts.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Search item (tomato, rice...)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </section>

      <div className="tabs">
        {CATEGORIES.map((c) => (
          <button
            key={c.key}
            className={category === c.key ? "tab active" : "tab"}
            onClick={() => setCategory(c.key)}
          >
            {c.label}
          </button>
        ))}
      </div>

      {data.latest_date && (
        <p className="muted center">
          Latest data: {data.latest_date} | Prices in {"\u20B9"} per kg
        </p>
      )}

      {error && <p className="error center">{error}</p>}
      {loading && <p className="muted center">Loading prices...</p>}
      {!loading && !error && districtId && data.items.length === 0 && (
        <p className="muted center">No prices found for this selection.</p>
      )}

      <div className="grid">
        {data.items.map((item) => (
          <PriceCard key={item.item_id} item={item} onClick={() => setSelected(item)} />
        ))}
      </div>

      {selected && (
        <HistoryModal
          item={selected}
          districtId={districtId}
          onClose={() => setSelected(null)}
        />
      )}

      <footer className="footer">
        Data source: Government of India Agmarknet (mandi prices) and manual updates.
        Mandi rates are wholesale rates, so shop prices can be a little higher.
      </footer>
    </div>
  );
}