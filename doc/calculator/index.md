---
title: Calculator
hide:
  - toc
---

<link rel="stylesheet" href="calculator.css">
<script src="coi-serviceworker.js"></script>
<script type="module" src="calculator.mjs"></script>

# Microstrip calculator

<div class="calc-intro">Two-layer, finite-ground quasi-static FEM. Dimensions are in mil (0.001 inch).</div>

<div class="calc-layout">
  <form id="calculator" class="calc-form">
    <div class="calc-section"><h2>Trace</h2><div class="calc-fields">
      <label>Bottom width W1 <span>mil</span><input name="w1" type="number" min="0.01" max="500" step="any" value="10" required></label>
      <label>Top width W2 <span>mil</span><input name="w2" type="number" min="0.01" max="500" step="any" value="5.6" required></label>
      <label>Thickness T <span>mil</span><input name="trace_thickness" type="number" min="0.01" max="500" step="any" value="1.8" required></label>
    </div></div>
    <div class="calc-section"><h2>Dielectric layers</h2><div class="calc-fields">
      <label>Lower height H1 <span>mil</span><input name="h1" type="number" min="0.01" max="500" step="any" value="2.97" required></label>
      <label>Lower permittivity Er1<input name="er1" type="number" min="1" max="100" step="any" value="4.2" required></label>
      <label>Upper height H2 <span>mil</span><input name="h2" type="number" min="0.01" max="500" step="any" value="3.53" required></label>
      <label>Upper permittivity Er2<input name="er2" type="number" min="1" max="100" step="any" value="4.2" required></label>
    </div></div>
    <details class="calc-advanced"><summary>Mesh settings</summary><div class="calc-fields">
      <label>Trace area factor<input name="trace_mesh_area_factor" type="number" min="10" max="400" step="any" value="50" required></label>
      <label>Far-field area factor<input name="far_mesh_area_factor" type="number" min="50" max="3200" step="any" value="400" required></label>
      <label>Finite element order<select name="order"><option value="2">P2</option><option value="1">P1</option></select></label>
    </div></details>
    <div class="calc-actions"><button type="submit" id="run">Calculate</button><button type="button" id="cancel" hidden>Cancel</button><button type="button" id="reset">Reset</button></div>
    <p id="status" class="calc-status" role="status" aria-live="polite">Ready</p>
  </form>
  <section class="calc-result" aria-labelledby="result-heading">
    <h2 id="result-heading">Results</h2>
    <div class="calc-primary"><span>Characteristic impedance</span><strong id="impedance">&mdash;</strong><span>ohm</span></div>
    <dl class="calc-metrics">
      <div><dt>Effective permittivity</dt><dd id="eeff">&mdash;</dd></div>
      <div><dt>Capacitance</dt><dd><span id="capacitance">&mdash;</span> pF/m</dd></div>
      <div><dt>Vacuum capacitance</dt><dd><span id="vacuum">&mdash;</span> pF/m</dd></div>
      <div><dt>Inductance</dt><dd><span id="inductance">&mdash;</span> nH/m</dd></div>
      <div><dt>Phase velocity</dt><dd><span id="velocity">&mdash;</span> m/s</dd></div>
      <div><dt>Mesh</dt><dd id="mesh">&mdash;</dd></div>
      <div><dt>Degrees of freedom</dt><dd id="dofs">&mdash;</dd></div>
    </dl>
    <button type="button" id="download" disabled>Download JSON</button>
    <img class="calc-diagram" src="../microstrip_geometry.svg" alt="Two dielectric layers, trapezoidal signal trace and ground">
  </section>
</div>

<p class="calc-note">Calculations run locally in your browser. The first run downloads the solver. Large meshes may need substantial memory. Check <a href="../validation/">mesh and domain convergence</a> for your application.</p>

<p class="calc-note">The browser mesher uses <a href="https://github.com/loumalouomega/GMSH-JS/tree/v0.4.0">gmsh-wasm 0.4.0</a>, distributed under GPL-2.0-or-later. See <a href="https://github.com/loumalouomega/GMSH-JS/blob/v0.4.0/LICENSE">its license</a> and the <a href="../development/#browser-calculator">runtime and build notes</a>.</p>
