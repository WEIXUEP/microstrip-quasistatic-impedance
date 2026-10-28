const form = document.querySelector('#calculator');
const status = document.querySelector('#status');
const run = document.querySelector('#run');
const download = document.querySelector('#download');
let worker, latest;
const resultIds = ['impedance','eeff','capacitance','vacuum','inductance','velocity','mesh','dofs'];
function setStatus(text, error = false) { status.textContent = text; status.classList.toggle('error', error); }
function clearResult() { latest = null; download.disabled = true; for (const id of resultIds) document.getElementById(id).textContent = '\u2014'; }
function busy(value) { run.disabled = value; document.querySelector('#cancel').hidden = !value; document.querySelector('#reset').disabled = value; for (const field of form.querySelectorAll('input,select')) field.disabled = value; }
function createWorker() {
  worker = new Worker(new URL('./worker.mjs', import.meta.url), {type:'module'});
  worker.onmessage = ({data}) => {
    if (data.type === 'progress') setStatus(data.text);
    if (data.type === 'error') { busy(false); worker.terminate(); worker = null; setStatus(`Calculation failed: ${data.message}`, true); }
    if (data.type === 'result') {
      latest = data.result; busy(false); download.disabled = false;
      document.getElementById('impedance').textContent = latest.characteristic_impedance_ohm.toFixed(4);
      document.getElementById('eeff').textContent = latest.effective_permittivity.toFixed(5);
      document.getElementById('capacitance').textContent = (latest.capacitance_F_per_m*1e12).toFixed(4);
      document.getElementById('vacuum').textContent = (latest.vacuum_capacitance_F_per_m*1e12).toFixed(4);
      document.getElementById('inductance').textContent = (latest.inductance_H_per_m*1e9).toFixed(4);
      document.getElementById('velocity').textContent = latest.phase_velocity_m_per_s.toExponential(5);
      document.getElementById('mesh').textContent = `${latest.vertices.toLocaleString()} vertices / ${latest.triangles.toLocaleString()} triangles`;
      document.getElementById('dofs').textContent = latest.dofs.toLocaleString();
      setStatus('Calculation complete.');
    }
  };
  worker.onerror = event => { busy(false); worker.terminate(); worker = null; setStatus(`Calculation failed: ${event.message}`, true); };
}
form.addEventListener('submit', event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const p = Object.fromEntries([...new FormData(form)].map(([key,value]) => [key,Number(value)]));
  if (p.trace_thickness >= p.h2) { setStatus('Trace thickness must be smaller than upper layer height H2.', true); return; }
  if (Math.max(p.w1,p.w2) >= 30*(p.h1+p.h2)) { setStatus('Trace width must be smaller than the substrate width.', true); return; }
  if (!crossOriginIsolated) { setStatus('Browser isolation is unavailable. Use HTTPS or localhost and allow service workers.', true); return; }
  clearResult(); busy(true); if (!worker) createWorker(); worker.postMessage(p); setStatus('Starting calculation...');
});
form.addEventListener('input', () => { if (latest) { clearResult(); setStatus('Inputs changed. Calculate again.'); } });
document.querySelector('#reset').addEventListener('click', () => { form.reset(); clearResult(); setStatus('Ready'); });
document.querySelector('#cancel').addEventListener('click', () => { if (worker) worker.terminate(); worker = null; busy(false); clearResult(); setStatus('Calculation canceled.'); });
download.addEventListener('click', () => {
  if (!latest) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(latest,null,2)+'\n'],{type:'application/json'}));
  const a = document.createElement('a'); a.href=url; a.download='microstrip-result.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
