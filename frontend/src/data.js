/**
 * Load results.json and map data for the demo.
 */

export async function loadResults() {
  try {
    const resp = await fetch('/data/results.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.warn('Failed to load results.json, using placeholder data:', e);
    return { maps: {}, results: {} };
  }
}
