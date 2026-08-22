async function getStatus() {
  const res = await fetch('/api/status');
  return res.json();
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function render(data) {
  const alive = data.workers.filter(w => w.alive).length;
  document.getElementById('throughput').textContent = formatNumber(data.throughput_estimate);
  document.getElementById('queue').textContent = formatNumber(data.queue_depth);
  document.getElementById('workers').textContent = `${alive}/${data.workers.length}`;
  document.getElementById('processed').textContent = formatNumber(data.processed);

  document.getElementById('workerList').innerHTML = data.workers.map(w => `
    <div class="worker">
      <div class="worker-main">
        <span class="dot ${w.alive ? 'up' : 'down'}"></span>
        <div>
          <b>Worker ${w.worker_id}</b>
          <div class="worker-meta">PID ${w.pid ?? '—'} · Restarts ${w.restarts}</div>
        </div>
      </div>
      <button class="kill" onclick="killWorker(${w.worker_id})">Terminate</button>
    </div>
  `).join('');

  document.getElementById('topology').innerHTML = `
    <div class="node"><b>Event Generator</b><span>synthetic telemetry</span></div>
    <div class="node"><b>Shared Queue</b><span>${formatNumber(data.queue_depth)} waiting</span></div>
    ${data.workers.map(w => `<div class="node"><b>Worker ${w.worker_id}</b><span>${w.alive ? 'healthy' : 'recovering'} · PID ${w.pid ?? '—'}</span></div>`).join('')}
    <div class="node"><b>Metrics</b><span>Prometheus compatible</span></div>
  `;
}

async function refresh() {
  try { render(await getStatus()); } catch (e) { console.error(e); }
}

async function generate() {
  const count = Number(document.getElementById('count').value);
  const label = document.getElementById('generatorResult');
  label.textContent = 'Submitting workload...';
  const res = await fetch(`/api/generate?count=${count}`, { method: 'POST' });
  const data = await res.json();
  label.textContent = `Accepted ${formatNumber(data.accepted)} · Rejected ${formatNumber(data.rejected)} · Submission rate ${formatNumber(data.submission_rate)} events/sec`;
  refresh();
}

async function killWorker(id) {
  const res = await fetch(`/api/chaos/kill/${id}`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) alert(data.detail || 'Chaos action failed');
  refresh();
}

async function resetSystem() {
  await fetch('/api/reset', { method: 'POST' });
  document.getElementById('generatorResult').textContent = 'System reset. All workers are healthy again.';
  refresh();
}

refresh();
setInterval(refresh, 1000);
