// Optional developer check using built-in Node assert; no frontend dependencies.
const assert = require('assert');
const {resolveGameQuery} = require('../web/game_search.js');
const games = [
  {source_game_id: 3, home_team: 'Texas', away_team: 'Wyoming', start_time_utc: '2023-09-16T23:00:00Z'},
  {source_game_id: 1, home_team: 'Texas', away_team: 'Rice', start_time_utc: '2023-09-02T19:30:00Z'},
  {source_game_id: 2, home_team: 'Alabama', away_team: 'Texas', start_time_utc: '2023-09-09T23:00:00Z'}
];
for (const [query, expected] of [
  ["Can you give me a briefing on Texas' 3rd game of the 23 season?", 3],
  ['Texas’s third game of 2023', 3],
  ['Game number 2', 2],
  ['Texas vs Alabama in 2023', 2],
  ['Rice', 1],
  ['First game of season 23', 1]
]) {
  assert.strictEqual(resolveGameQuery(query, games).source_game_id, expected);
  console.log('PASS:', query);
}
for (const query of ['Texas vs Alabama in 2024', 'Texas game 0', 'Texas 15th game',
  'Texas vs Rice and Alabama', 'Brief Texas', 'Texas third game against Alabama',
  'Texas first game and third game', 'Predict Texas vs Alabama', 'x'.repeat(501)]) {
  assert.throws(() => resolveGameQuery(query, games));
  console.log('PASS: reject/clarify:', query.slice(0, 65));
}
assert.deepStrictEqual(games.map(game => game.source_game_id), [3, 1, 2]);

const catalog = require('../web/team_aliases.json');
const opponents = catalog.teams.filter(team => team.in_initial_dataset).map((team, index) => ({
  source_game_id: 100 + index, home_team: 'Texas', away_team: team.canonical_name,
  start_time_utc: `2023-09-${String(index + 1).padStart(2, '0')}T00:00:00Z`
}));
let aliasChecks = 0;
for (const team of catalog.teams.filter(team => team.in_initial_dataset)) {
  const expected = opponents.find(game => game.away_team === team.canonical_name);
  for (const alias of [team.canonical_name].concat(team.aliases, team.mascot_aliases || [])) {
    const candidates = catalog.teams.filter(t => t.in_initial_dataset && [t.canonical_name].concat(t.aliases, t.mascot_aliases || []).includes(alias));
    if (candidates.length > 1) continue; // Shared alias cases are checked explicitly below.
    assert.strictEqual(resolveGameQuery(`Brief Texas vs ${alias}`, opponents, catalog).source_game_id, expected.source_game_id);
    aliasChecks++;
  }
}
const expectOpponent = (query, name, list = opponents) => assert.strictEqual(resolveGameQuery(query, list, catalog).away_team, name);
expectOpponent('Texas vs brigham   young UNIVERSITY', 'BYU');
expectOpponent('Texas vs B.Y.U.', 'BYU');
expectOpponent('Texas vs o.s.u.', 'Oklahoma State');
expectOpponent('Texas vs K—State', 'Kansas State');
expectOpponent('Texas vs University of Washington (UW)', 'Washington');
expectOpponent('Texas vs University of Wyoming (UW)', 'Wyoming');
expectOpponent('Texas vs Oklahoma State', 'Oklahoma State');
expectOpponent('Texas vs Kansas State University', 'Kansas State');
expectOpponent('Texas vs UW', 'Washington', opponents.filter(game => game.away_team !== 'Wyoming'));
assert.throws(() => resolveGameQuery('Texas vs UW', opponents, catalog), /More than one/);
assert.throws(() => resolveGameQuery('Texas vs Oklahoma and Oklahoma State', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs Kansas and Kansas State', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs BYU and OSU', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs Ohio State University', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs COSUMER', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs OSU', opponents.concat({source_game_id: 999, home_team:'Texas', away_team:'Ohio State', start_time_utc:'2023-12-01T00:00:00Z'}), catalog), /More than one/);
assert.throws(() => resolveGameQuery('Texas vs UW', opponents.concat({...opponents[0], source_game_id: 999, away_team:'Washington'}), catalog), /More than one/);
console.log(`PASS: ${aliasChecks} canonical/alias checks plus 17 normalization, context, ambiguity, and collision checks.`);

expectOpponent('Brief Texas vs Cougs', 'BYU');
expectOpponent('Brief Texas vs Coogs', 'Houston');
expectOpponent('Brief Texas vs Cowpokes', 'Oklahoma State');
expectOpponent('Brief Texas vs Oklahoma State Cowboys', 'Oklahoma State');
expectOpponent('Brief Texas vs Wyoming Pokes', 'Wyoming');
expectOpponent('Brief Texas vs BYU Cougars', 'BYU');
expectOpponent('Brief Texas vs Houston Cougars', 'Houston');
expectOpponent('Brief Texas third game vs Cowboys', 'Wyoming');
for (const nickname of ['Cowboys', 'Pokes', 'Cougars']) {
  assert.throws(() => resolveGameQuery(`Texas vs ${nickname}`, opponents, catalog), /More than one/);
}
assert.throws(() => resolveGameQuery('Texas vs Wyoming Cougars', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs Pokes and Cougs', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs Cowboys third game and Oklahoma State', opponents, catalog));
assert.throws(() => resolveGameQuery('Texas vs Cougs', opponents.concat({source_game_id:999,home_team:'Texas',away_team:'Washington State',start_time_utc:'2023-12-01T00:00:00Z'}), catalog), /More than one/);
assert.throws(() => resolveGameQuery('Texas vs supercowboys', opponents, catalog));
console.log('PASS: 16 additional mascot/nickname context and ambiguity cases.');
