import { renderMap } from './renderer.js';
import { loadResults } from './data.js';

const state = {
  results: null,
  currentMap: 2,
  currentMethod: 'ga',
  alpha: 1.0,
  beta: 1.0,
  gamma: 1.0,
};

function updateDisplay() {
  if (!state.results) return;
  const mapData = state.results.maps?.[`map${state.currentMap}`];
  const methodResult = state.results.results?.[`map${state.currentMap}`]?.[state.currentMethod];
  // Only pass method result to renderer if it has valid route data
  const validResult = (methodResult && methodResult.route && !methodResult.error) ? methodResult : null;
  if (mapData) {
    renderMap(document.getElementById('map-canvas'), mapData, validResult, state);
  }
  updateCostPanel(validResult);
  updateComparisonTable();
}

function updateCostPanel(result) {
  const setVal = (id, val) => {
    document.getElementById(id).textContent = (val != null && isFinite(val)) ? val.toFixed(1) : '—';
  };
  if (result && result.total_cost != null) {
    setVal('cost-route', result.route_cost);
    setVal('cost-walk', result.walk_cost);
    setVal('cost-stop', result.stop_cost);
    setVal('cost-total', result.total_cost);
    document.getElementById('cost-coverage').textContent =
      result.coverage != null ? `${(result.coverage * 100).toFixed(1)}%` : '—';
  } else {
    ['cost-route', 'cost-walk', 'cost-stop', 'cost-total', 'cost-coverage'].forEach(
      id => (document.getElementById(id).textContent = '—')
    );
  }
}

function updateComparisonTable() {
  const tbody = document.querySelector('#comparison-table tbody');
  tbody.innerHTML = '';
  const methods = ['baseline', 'greedy', 'ga', 'sa', 'milp'];
  const mapResults = state.results?.results?.[`map${state.currentMap}`];
  if (!mapResults) return;
  methods.forEach(m => {
    const r = mapResults[m];
    const tr = document.createElement('tr');
    const highlight = m === state.currentMethod ? ' style="color:#64b5f6;font-weight:bold"' : '';
    const costStr = (r && r.total_cost != null) ? r.total_cost.toFixed(1) : 'N/A';
    const covStr = (r && r.coverage != null) ? (r.coverage * 100).toFixed(1) + '%' : 'N/A';
    tr.innerHTML = `
      <td${highlight}>${m.toUpperCase()}</td>
      <td${highlight}>${costStr}</td>
      <td${highlight}>${covStr}</td>
    `;
    tbody.appendChild(tr);
  });
}

function setupControls() {
  document.getElementById('map-select').addEventListener('change', e => {
    state.currentMap = parseInt(e.target.value);
    updateDisplay();
  });

  document.getElementById('method-select').addEventListener('change', e => {
    state.currentMethod = e.target.value;
    updateDisplay();
  });

  const sliders = [
    { id: 'alpha-slider', valId: 'alpha-val', key: 'alpha' },
    { id: 'beta-slider', valId: 'beta-val', key: 'beta' },
    { id: 'gamma-slider', valId: 'gamma-val', key: 'gamma' },
  ];

  sliders.forEach(({ id, valId, key }) => {
    const slider = document.getElementById(id);
    slider.addEventListener('input', () => {
      state[key] = parseFloat(slider.value);
      document.getElementById(valId).textContent = state[key].toFixed(1);
      recalcCosts();
    });
  });
}

function recalcCosts() {
  // Recalculate total cost with current alpha/beta/gamma
  const mapResults = state.results?.results?.[`map${state.currentMap}`];
  if (!mapResults) return;
  const methods = ['baseline', 'greedy', 'ga', 'sa', 'milp'];
  methods.forEach(m => {
    const r = mapResults[m];
    if (r && r.raw_route_cost != null) {
      r.total_cost =
        state.alpha * r.raw_route_cost +
        state.beta * r.raw_walk_cost +
        state.gamma * r.raw_stop_cost;
      r.route_cost = state.alpha * r.raw_route_cost;
      r.walk_cost = state.beta * r.raw_walk_cost;
      r.stop_cost = state.gamma * r.raw_stop_cost;
    }
  });
  const current = mapResults[state.currentMethod];
  updateCostPanel(current);
  updateComparisonTable();
}

async function init() {
  setupControls();
  state.results = await loadResults();
  updateDisplay();
}

init();
