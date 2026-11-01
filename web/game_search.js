'use strict';
// Resolve only against already-imported games. No model, SQL, or free-form prompt.
function resolveGameQuery(question, games, catalog = {teams: []}) {
  if (typeof question !== 'string' || !question.trim() || question.length > 500) {
    throw new Error('Enter a request of 1–500 characters.');
  }
  const normalize = value => value.toLowerCase().replace(/[’']/g, '').replace(/\./g, '').replace(/[^a-z0-9]+/g, ' ').trim();
  const text = normalize(question);
  const fullYears = text.match(/\b(?:19|20)\d{2}\b/g) || [];
  const shortYears = Array.from(text.matchAll(/\b(\d{2})\s+season\b|\bseason\s+(\d{2})\b/g), m => '20' + (m[1] || m[2]));
  if (fullYears.concat(shortYears).some(year => year !== '2023')) {
    throw new Error('Only Texas’s 2023 season is imported. Try “Texas vs Alabama in 2023”.');
  }
  if (/\b(predict|prediction|preview|upcoming)\b/.test(text)) {
    throw new Error('This demo supports historical postgame briefings. Try an opponent or game number from 2023.');
  }
  const ordered = games.slice().sort((a, b) => a.start_time_utc.localeCompare(b.start_time_utc) || a.source_game_id - b.source_game_id);
  const ordinalWords = {first: 1, second: 2, third: 3, fourth: 4, fifth: 5, sixth: 6, seventh: 7, eighth: 8, ninth: 9, tenth: 10, eleventh: 11, twelfth: 12, thirteenth: 13, fourteenth: 14};
  const numeric = Array.from(text.matchAll(/\b(\d{1,2})(?:st|nd|rd|th)\s+game\b|\bgame\s*(?:number\s*)?(\d{1,2})\b/g), m => Number(m[1] || m[2]));
  const words = Array.from(text.matchAll(/\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth)\s+game\b/g), m => ordinalWords[m[1]]);
  const numbers = numeric.concat(words);
  if (new Set(numbers).size > 1) throw new Error('Please request one game number at a time.');
  const opponent = game => game.home_team === 'Texas' ? game.away_team : game.home_team;
  const names = new Map(catalog.teams.map(team => [team.canonical_name, team.aliases.concat(team.mascot_aliases || [])]));
  ordered.forEach(game => { if (!names.has(opponent(game))) names.set(opponent(game), []); });
  const hits = [];
  for (const [canonical, aliases] of names) {
    for (const alias of new Set([canonical].concat(aliases).map(normalize))) {
      const regex = new RegExp('\\b' + alias + '\\b', 'g'); // alias normalization removes regex syntax
      for (const match of text.matchAll(regex)) hits.push({canonical, start: match.index, end: match.index + alias.length});
    }
  }
  // Longest overlapping mention wins; separate mentions remain separate constraints.
  const longest = hits.filter(hit => !hits.some(other => other.start <= hit.start && other.end >= hit.end && other.end - other.start > hit.end - hit.start));
  const groups = new Map();
  for (const hit of longest) {
    const key = `${hit.start}:${hit.end}`;
    if (!groups.has(key)) groups.set(key, new Set());
    groups.get(key).add(hit.canonical);
  }
  const mentions = Array.from(groups.values());
  const matches = ordered.filter(game => mentions.length && mentions.every(group => group.has(opponent(game))));
  if (numbers.length) {
    const game = ordered[numbers[0] - 1];
    if (!game) throw new Error(`Choose game 1 through ${ordered.length} of the 2023 season.`);
    if (mentions.length && !matches.some(g => g.source_game_id === game.source_game_id)) {
      throw new Error('The game number and opponent do not match. Please use one or check the season order.');
    }
    return game;
  }
  if (matches.length > 1) throw new Error(`More than one imported game matches: ${Array.from(new Set(matches.map(opponent))).join(', ')}. Please use a full opponent name or game number.`);
  if (matches.length !== 1) throw new Error('Please name one imported opponent or a game number, such as “Texas’s third game of the 23 season”.');
  return matches[0];
}
if (typeof module !== 'undefined') module.exports = {resolveGameQuery};
