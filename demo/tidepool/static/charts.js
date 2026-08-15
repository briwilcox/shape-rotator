// Canvas sparkline rendering for tank temperature history.
import { getReadings } from "./api.js";

export async function drawSparklines(container) {
  const readings = await getReadings();
  for (const [tank, rows] of Object.entries(readings)) {
    const canvas = document.createElement("canvas");
    canvas.width = 240;
    canvas.height = 48;
    canvas.title = tank;
    container.appendChild(canvas);
    sparkline(canvas, rows.map((r) => r.temp_c));
  }
}

function sparkline(canvas, values) {
  const ctx = canvas.getContext("2d");
  if (!values.length) return;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  ctx.strokeStyle = "#3aa0ff";
  ctx.beginPath();
  values.forEach((v, i) => {
    const x = (i / (values.length - 1 || 1)) * canvas.width;
    const y = canvas.height - ((v - min) / span) * canvas.height;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
}
