import { mesh } from './mesh.mjs';

let gmsh, py, solverLoaded = false;
const progress = text => postMessage({ type: 'progress', text });

async function initialize() {
  if (!gmsh) {
    progress('Loading Gmsh...');
    const { default: init } = await import('./vendor/gmsh.mjs');
    gmsh = await init();
  }
  if (!py) {
    progress('Loading Python and numerical libraries...');
    const { loadPyodide } = await import('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs');
    py = await loadPyodide();
    await py.loadPackage(['numpy', 'scipy', 'micropip']);
    await py.runPythonAsync('import micropip; await micropip.install("scikit-fem==11.0.0")');
  }
  if (!solverLoaded) {
    const response = await fetch('./solver.py');
    if (!response.ok) throw new Error('Solver source is unavailable. The site build may be incomplete.');
    py.globals.set('solver_source', await response.text());
    py.runPython(`
import sys, types
sys.modules['gmsh'] = types.ModuleType('gmsh')
solver = types.ModuleType('browser_solver')
sys.modules['browser_solver'] = solver
exec(compile(solver_source, 'microstrip_quasistatic.py', 'exec'), solver.__dict__)
`);
    solverLoaded = true;
  }
}

onmessage = async ({ data: p }) => {
  try {
    await initialize();
    progress('Generating mesh...');
    const data = await mesh(gmsh, p);
    py.globals.set('mesh_json', JSON.stringify(data));
    py.globals.set('params_json', JSON.stringify(p));
    progress('Solving two electrostatic problems...');
    const result = py.runPython(`
import json, numpy as np
from scipy.constants import c
d=json.loads(mesh_json)
params=json.loads(params_json)
order=params.pop('order')
pts=np.array(d['points']); tri=np.array(d['triangles']); used=np.unique(tri)
mapping=np.full(len(pts),-1,dtype=int); mapping[used]=np.arange(len(used))
mesh=solver.MeshData(pts[used],mapping[tri],np.array(d['er']),mapping[np.intersect1d(d['signal'],used)],mapping[np.intersect1d(d['ground'],used)])
p=solver.MicrostripGeometry(**params)
potential,C=solver.solve_electrostatic(mesh,p,False,order)
_,C0=solver.solve_electrostatic(mesh,p,True,order)
json.dumps({'geometry':params,'order':order,'vertices':len(mesh.points),'triangles':len(mesh.triangles),'dofs':len(potential),'capacitance_F_per_m':C,'vacuum_capacitance_F_per_m':C0,'effective_permittivity':C/C0,'inductance_H_per_m':1/(c*c*C0),'phase_velocity_m_per_s':c/np.sqrt(C/C0),'characteristic_impedance_ohm':1/(c*np.sqrt(C*C0))})
`);
    postMessage({ type: 'result', result: JSON.parse(result) });
  } catch (error) {
    console.error(error);
    postMessage({ type: 'error', message: error?.message || String(error) });
  }
};
