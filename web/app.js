'use strict';
// Start fresh on reload instead of restoring the previous results scroll position.
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
window.addEventListener('pageshow', () => window.scrollTo(0, 0));
const el = id => document.getElementById(id);
let config;
let hasGames = false;
let busy = false;
let importedGames = [];
let teamAliases;
async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok || data.status === 'error') throw new Error(data.error || 'Game data is unavailable. Check local MySQL.');
  return data;
}
function status(text) { el('status').textContent = text; }
function showResults() {
  el('results').scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    block: 'start'
  });
}
function render(result, sample) {
  el('output').hidden = false;
  el('empty').hidden = true;
  el('result-title').textContent = result.briefing.title;
  el('result-mode').textContent = sample ? 'SAVED SAMPLE' : 'LIVE BRIEFING';
  el('claims').replaceChildren();
  for (const claim of result.briefing.claims) {
    const li = document.createElement('li');
    li.textContent = claim.text;
    const citation = document.createElement('span');
    citation.className = 'citation';
    citation.textContent = claim.evidence_ref;
    li.append(citation);
    el('claims').append(li);
  }
  el('limits').replaceChildren();
  for (const text of result.briefing.limitations) {
    const li = document.createElement('li'); li.textContent = text; el('limits').append(li);
  }
  el('evidence').textContent = JSON.stringify(result.evidence, null, 2);
  el('usage').textContent = `${result.model_calls} model requests · ${result.reported_tokens.toLocaleString()} reported tokens${sample ? ' · Original saved run; no request made now.' : ' · Claims should be checked against the evidence.'}`;
  status(sample ? 'Saved October 30 sample. This is not a new generation.' : 'Briefing ready. Inspect the evidence and limitations below.');
  showResults();
}
async function load() {
  try {
    config = await api('/api/config');
    teamAliases = await api('/api/team-aliases');
    el('mode').textContent = config.live_enabled ? 'Live generation enabled · Luna / low effort' : 'Preview mode · Live generation disabled';
    const data = await api('/api/games');
    importedGames = data.games;
    el('game').replaceChildren();
    for (const game of data.games) {
      const option = document.createElement('option');
      option.value = game.source_game_id;
      option.textContent = `${game.away_team} at ${game.home_team} · ${game.start_time_utc.slice(0, 10)}`;
      el('game').append(option);
    }
    hasGames = data.games.length > 0;
    if (data.games.some(g => g.source_game_id === 401520183)) el('game').value = '401520183';
    el('game').disabled = !hasGames;
    el('question').disabled = !hasGames;
    el('generate').disabled = !config.live_enabled || !hasGames;
    if (!hasGames) status('No imported games found. The saved sample is still available.');
  } catch (error) { status(`${error.message} You can still view the saved sample.`); }
}
el('sample').addEventListener('click', async () => {
  showResults();
  try { render(await api('/api/sample'), true); } catch (error) { status(error.message); }
});
el('game').addEventListener('change', () => { el('question').value = ''; });
el('question').addEventListener('keydown', event => {
  if (event.key === 'Enter') { event.preventDefault(); el('generate').click(); }
});
el('generate').addEventListener('click', async () => {
  if (busy || !config || !config.live_enabled || !hasGames) return;
  let selectedGame;
  try {
    selectedGame = el('question').value.trim() ? resolveGameQuery(el('question').value, importedGames, teamAliases) : importedGames.find(game => game.source_game_id === Number(el('game').value));
    if (!selectedGame) throw new Error('Choose an imported game.');
    el('game').value = String(selectedGame.source_game_id);
  } catch (error) { status(error.message); showResults(); return; }
  busy = true;
  el('question').disabled = true;
  el('generate').disabled = true; el('sample').disabled = true; el('game').disabled = true;
  el('output').hidden = true; el('empty').hidden = true;
  el('result-mode').textContent = 'RESEARCH → WRITE';
  status(`Matched: ${selectedGame.away_team} at ${selectedGame.home_team} (${selectedGame.start_time_utc.slice(0, 10)}). Researching records and writing your briefing…`);
  showResults();
  try {
    render(await api('/api/briefing', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Demo-Token': config.token}, body: JSON.stringify({source_game_id: Number(el('game').value)})}), false);
  } catch (error) { status(error.message); el('result-mode').textContent = 'STOPPED'; }
  finally {
    busy = false; el('generate').disabled = false; el('sample').disabled = false; el('game').disabled = false; el('question').disabled = false;
  }
});
load();
