/**
 * 2D Canvas renderer for city map, routes, stops, and passengers.
 */

const COLORS = {
  background: '#1a1f2e',
  grid: '#252b3b',
  forbidden: '#2d2d2d',
  forbiddenBorder: '#424242',
  terrain1: '#1a2332',  // cost 1 (default)
  terrain2: '#1a3040',  // cost 2
  terrain3: '#1a3d4d',  // cost 3+
  terrainHigh: '#2d4a3d', // high cost
  route: '#2196f3',
  routeGlow: 'rgba(33,150,243,0.3)',
  stop: '#ff9800',
  stopGlow: 'rgba(255,152,0,0.4)',
  passenger: '#e0e0e0',
  passengerLine: 'rgba(255,152,0,0.2)',
  endpointA: '#4caf50',
  endpointB: '#f44336',
};

export function renderMap(canvas, mapData, methodResult, state) {
  if (!mapData) return;

  const gridSize = mapData.grid_size || 50;
  const cellSize = Math.min(
    Math.floor((window.innerWidth - 380) / gridSize),
    Math.floor((window.innerHeight - 160) / gridSize),
    14
  );
  const size = gridSize * cellSize;
  canvas.width = size;
  canvas.height = size;

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, size, size);

  // Draw terrain
  drawTerrain(ctx, mapData, gridSize, cellSize);

  // Draw forbidden zones
  drawForbiddenZones(ctx, mapData, gridSize, cellSize);

  // Draw grid lines
  drawGrid(ctx, gridSize, cellSize, size);

  // Draw passengers
  drawPassengers(ctx, mapData, methodResult, gridSize, cellSize);

  // Draw route
  if (methodResult) {
    drawRoute(ctx, methodResult, cellSize);
    drawStops(ctx, methodResult, cellSize);
    drawPassengerLines(ctx, mapData, methodResult, cellSize);
  }

  // Draw endpoints
  drawEndpoints(ctx, mapData, cellSize);
}

function drawTerrain(ctx, mapData, gridSize, cellSize) {
  const terrain = mapData.terrain;
  if (!terrain) {
    ctx.fillStyle = COLORS.terrain1;
    ctx.fillRect(0, 0, gridSize * cellSize, gridSize * cellSize);
    return;
  }

  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      const cost = terrain[y]?.[x] || 1;
      if (cost <= 1) ctx.fillStyle = COLORS.terrain1;
      else if (cost === 2) ctx.fillStyle = COLORS.terrain2;
      else if (cost <= 4) ctx.fillStyle = COLORS.terrain3;
      else ctx.fillStyle = COLORS.terrainHigh;
      ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
    }
  }
}

function drawForbiddenZones(ctx, mapData, gridSize, cellSize) {
  const forbidden = mapData.forbidden;
  if (!forbidden) return;

  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      if (forbidden[y]?.[x]) {
        ctx.fillStyle = COLORS.forbidden;
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        ctx.strokeStyle = COLORS.forbiddenBorder;
        ctx.lineWidth = 0.5;
        ctx.strokeRect(x * cellSize, y * cellSize, cellSize, cellSize);
      }
    }
  }
}

function drawGrid(ctx, gridSize, cellSize, size) {
  ctx.strokeStyle = COLORS.grid;
  ctx.lineWidth = 0.3;
  for (let i = 0; i <= gridSize; i++) {
    ctx.beginPath();
    ctx.moveTo(i * cellSize, 0);
    ctx.lineTo(i * cellSize, size);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, i * cellSize);
    ctx.lineTo(size, i * cellSize);
    ctx.stroke();
  }
}

function drawPassengers(ctx, mapData, methodResult, gridSize, cellSize) {
  const passengers = mapData.passengers;
  if (!passengers) return;

  ctx.fillStyle = COLORS.passenger;
  passengers.forEach(([x, y]) => {
    const cx = x * cellSize + cellSize / 2;
    const cy = y * cellSize + cellSize / 2;
    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(cellSize * 0.2, 2), 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawRoute(ctx, result, cellSize) {
  const route = result.route;
  if (!route || route.length < 2) return;

  // Glow
  ctx.strokeStyle = COLORS.routeGlow;
  ctx.lineWidth = cellSize * 0.6;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(route[0][0] * cellSize + cellSize / 2, route[0][1] * cellSize + cellSize / 2);
  for (let i = 1; i < route.length; i++) {
    ctx.lineTo(route[i][0] * cellSize + cellSize / 2, route[i][1] * cellSize + cellSize / 2);
  }
  ctx.stroke();

  // Main line
  ctx.strokeStyle = COLORS.route;
  ctx.lineWidth = Math.max(cellSize * 0.25, 2);
  ctx.beginPath();
  ctx.moveTo(route[0][0] * cellSize + cellSize / 2, route[0][1] * cellSize + cellSize / 2);
  for (let i = 1; i < route.length; i++) {
    ctx.lineTo(route[i][0] * cellSize + cellSize / 2, route[i][1] * cellSize + cellSize / 2);
  }
  ctx.stroke();
}

function drawStops(ctx, result, cellSize) {
  const stops = result.stops;
  if (!stops) return;

  stops.forEach(([x, y]) => {
    const cx = x * cellSize + cellSize / 2;
    const cy = y * cellSize + cellSize / 2;

    // Glow
    ctx.fillStyle = COLORS.stopGlow;
    ctx.beginPath();
    ctx.arc(cx, cy, cellSize * 0.6, 0, Math.PI * 2);
    ctx.fill();

    // Stop marker
    ctx.fillStyle = COLORS.stop;
    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(cellSize * 0.35, 3), 0, Math.PI * 2);
    ctx.fill();
  });
}

function drawPassengerLines(ctx, mapData, result, cellSize) {
  const passengers = mapData.passengers;
  const stops = result.stops;
  if (!passengers || !stops || stops.length === 0) return;

  ctx.strokeStyle = COLORS.passengerLine;
  ctx.lineWidth = 0.5;
  ctx.setLineDash([2, 3]);

  passengers.forEach(([px, py]) => {
    // Find nearest stop
    let minDist = Infinity;
    let nearestStop = stops[0];
    stops.forEach(([sx, sy]) => {
      const d = Math.abs(px - sx) + Math.abs(py - sy);
      if (d < minDist) {
        minDist = d;
        nearestStop = [sx, sy];
      }
    });

    if (minDist <= 15) {
      const pcx = px * cellSize + cellSize / 2;
      const pcy = py * cellSize + cellSize / 2;
      const scx = nearestStop[0] * cellSize + cellSize / 2;
      const scy = nearestStop[1] * cellSize + cellSize / 2;
      ctx.beginPath();
      ctx.moveTo(pcx, pcy);
      ctx.lineTo(scx, scy);
      ctx.stroke();
    }
  });

  ctx.setLineDash([]);
}

function drawEndpoints(ctx, mapData, cellSize) {
  const [ax, ay] = mapData.start || [0, 0];
  const [bx, by] = mapData.end || [0, 0];

  // Endpoint A
  const acx = ax * cellSize + cellSize / 2;
  const acy = ay * cellSize + cellSize / 2;
  ctx.fillStyle = COLORS.endpointA;
  ctx.beginPath();
  ctx.arc(acx, acy, Math.max(cellSize * 0.5, 5), 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.font = `bold ${Math.max(cellSize * 0.6, 8)}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('A', acx, acy);

  // Endpoint B
  const bcx = bx * cellSize + cellSize / 2;
  const bcy = by * cellSize + cellSize / 2;
  ctx.fillStyle = COLORS.endpointB;
  ctx.beginPath();
  ctx.arc(bcx, bcy, Math.max(cellSize * 0.5, 5), 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#fff';
  ctx.fillText('B', bcx, bcy);
}
