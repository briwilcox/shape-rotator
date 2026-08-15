// Frontend entrypoint: wires the dashboard together.
import { getSummary, postReading } from "./api.js";
import { drawSparklines } from "./charts.js";

async function refresh() {
  const summary = await getSummary();
  const list = document.getElementById("summary");
  list.innerHTML = "";
  for (const row of summary) {
    const li = document.createElement("li");
    li.textContent = `${row.tank}: ${row.mean_temp_c}°C over ${row.samples} samples`;
    list.appendChild(li);
  }
  await drawSparklines(document.getElementById("charts"));
}

document.getElementById("log-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  await postReading(form.get("tank"), Number(form.get("temp")), Number(form.get("ph")));
  refresh();
});

refresh();
