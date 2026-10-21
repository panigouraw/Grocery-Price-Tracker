const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function get(path, params = {}) {
  const url = new URL(BASE + path);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, value);
    }
  });
  const res = await fetch(url);
  if (!res.ok) throw new Error("API error " + res.status);
  return res.json();
}

export const getStates = () => get("/states");
export const getDistricts = (stateId) =>
  get("/districts", { state_id: stateId });
export const getPrices = (districtId, category, q) =>
  get("/prices", { district_id: districtId, category, q });
export const getHistory = (itemId, districtId, days = 30) =>
  get("/history", { item_id: itemId, district_id: districtId, days });
