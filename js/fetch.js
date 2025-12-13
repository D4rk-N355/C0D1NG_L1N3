// fetch.js
const sheetId = "1-a9qG20lKM0pa_1z1E7BxxvVriaNE1VFChEFyEpk0-0";
const sheetName = "data";
const sheetUrl = `https://docs.google.com/spreadsheets/d/${sheetId}/gviz/tq?sheet=${sheetName}&tqx=out:json`;

export async function fetchData() {
  try {
    const res = await fetch(sheetUrl);
    const text = await res.text();
    const json = JSON.parse(text.slice(47, -2)); // 用 slice 取代 substr
    return json.table.rows; // ✅ 回傳 rows
  } catch (err) {
    console.error("Fetch error:", err);
    throw err;
  }
}