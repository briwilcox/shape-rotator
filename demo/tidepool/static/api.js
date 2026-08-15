// Thin fetch wrapper for the tidepool API.
export async function getReadings() {
  const res = await fetch("/api/readings");
  return res.json();
}

export async function getSummary() {
  const res = await fetch("/api/summary");
  return res.json();
}

export async function postReading(tank, tempC, ph) {
  const res = await fetch("/api/reading", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tank, temp_c: tempC, ph }),
  });
  return res.json();
}
