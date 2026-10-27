# CFBD Source Validation

## Scope and Evidence

Initial sample: Texas’s 2023 schedule and results, including postseason, fetched using `scripts/fetch_games.py`. Team-statistics validation is recorded below. MySQL imports have not been validated yet.

- Source: CollegeFootballData, `GET https://api.collegefootballdata.com/games`
- Parameters: `year=2023`, `team=Texas`, `seasonType=both`
- Retrieved: October 26, 2026, 8:56 p.m. America/Chicago (`2026-10-27T01:56:48.114714+00:00`)
- HTTP status: 200
- Response size: 11,089 bytes
- SHA-256: `934b475693694dded5befa4cb0c9899d168dd3c0ae8005149f893202e797fc3f`
- Private evidence directory: `data/raw/cfbd-games-20261027T015648114714Z/`, containing `response.json` and `metadata.json`
- Comparison reference: [Texas Athletics’ official 2023 schedule](https://texaslonghorns.com/sports/football/schedule/text/2023)

Original responses remain outside Git. This report records the method and findings without publishing the raw dataset or credentials. The fingerprint identifies the saved response and can detect later changes; it does not prove the source’s accuracy.

## Checks and Findings

The importer performed structural checks. Codex then compared the saved records with the official schedule; this was a manual comparison, not an automated regression test.

| Check | Finding |
|---|---|
| Response structure | Nonempty JSON list containing game objects |
| Game identifiers | 14 integer IDs, no duplicates |
| Requested coverage | Each record identifies Texas and season 2023 |
| Completion and scores | All games marked completed; final scores are nonnegative integers |
| Schedule completeness | All 14 official games present; no extra games |
| Opponents and results | All opponents and final scores match the official schedule |
| Dates | All match after conversion from UTC to America/Chicago |
| Site classification | Home/away/neutral matches when `neutralSite` takes precedence over designated home/away teams |
| Overall record | 12 wins and 2 losses, matching the official schedule |

## Interpretation Rules

- Preserve UTC timestamps and convert to the chosen display time zone. For example, Wyoming’s September 17 UTC timestamp is September 16 in Central time. The Sugar Bowl’s January 2, 2024 UTC timestamp is January 1 locally and belongs to season 2023.
- Preserve CFBD’s season classification. It labels the December 2 Big 12 Championship `regular` and the Sugar Bowl `postseason`; the single postseason record does not mean the conference championship is missing.
- Designated home and away teams do not establish the physical site. Use the neutral-site flag when presenting location context.
- Matching counts alone cannot establish completeness: compare the actual opponents, dates, and scores.

## Decision and Remaining Work

CFBD passes the initial schedule/results evaluation. The team-statistics evaluation and scope decision appear below. Next, finalize the initial schema for the selected core fields.

API authentication succeeded. Database authorization, repeatable MySQL imports, restricted MCP tools, and agent behavior have not yet been tested. No claim about those controls follows from this source validation.

## Team Game Statistics Evaluation

Sample: `data/raw/cfbd-team-stats-20261027T020832174803Z/response.json`, fetched from `/games/teams` with the same season/team parameters. Checks used the saved files without additional API calls.

- All 14 schedule IDs have statistics for both teams (28 team-game records), with matching team identities and scores.
- There are 35 distinct categories across the dataset. Categories are not uniformly present; absent values must not automatically become zero.
- No supplied stat strings are empty. All supplied values match the inspected formats: signed integer/decimal, paired counts such as `24-38`, or possession time in `minutes:seconds` format.
- For all 28 records, rushing yards plus net passing yards equals total yards; fumbles lost plus interceptions thrown equals turnovers.
- For all 14 games, both teams’ possession times sum to 60 minutes. This is an observation for this sample, not a universal validation rule for overtime games.
- Categories present in all 28 records include first downs, total/passing/rushing yards, rushing attempts, completions-attempts, third/fourth-down efficiency, penalties-yards, turnovers, fumbles lost, interceptions thrown, and possession time.
- Sparse categories include defensive statistics (many present in 26 records), interception-return statistics (18), kickoff-return statistics (25), and punt-return statistics (19).

### Official Box-Score Spot Checks

Compared both teams in [Texas–Alabama](https://texaslonghorns.com/sports/football/stats/2023/alabama/boxscore/15529) and [Texas–Washington](https://texaslonghorns.com/sports/football/stats/2023/washington/boxscore/16073). First downs, total/passing/rushing yards, rushing attempts, completions-attempts, interceptions thrown, fumbles lost, penalties-yards, third/fourth-down conversions, and possession time match in these four team-game records. These are manual spot checks, not verification of every category in every game.

A discrepancy was found outside the proposed core fields: CFBD reports Texas `kickReturns=9` against Washington; the official box score lists 7. Both report 132 kickoff-return yards. Cause unresolved. Preserve the original data and exclude return statistics from the initial normalized briefing fields rather than silently correcting them.

### Initial Scope Decision

Proceed with CFBD for schedules/results and the core team statistics spot-checked above. Convert paired strings into separate counts and possession time into seconds during normalization; preserve source values in the original files. Do not assume absent optional categories are zero. Defer return and detailed defensive statistics. Full statistical accuracy across all games remains unverified.
