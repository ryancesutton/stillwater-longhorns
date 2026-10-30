-- Local MySQL 8.4 setup. Accounts are created separately; no passwords here.
-- Definer can read only the specified project data; it cannot log in.
GRANT SELECT ON stillwater.teams TO 'stillwater_view_owner'@'localhost';
GRANT SELECT ON stillwater.games TO 'stillwater_view_owner'@'localhost';
GRANT SELECT ON stillwater.team_game_stats TO 'stillwater_view_owner'@'localhost';
GRANT SELECT (ingestion_run_id, source, endpoint, source_retrieved_at_utc, response_sha256)
    ON stillwater.ingestion_runs TO 'stillwater_view_owner'@'localhost';

CREATE DEFINER='stillwater_view_owner'@'localhost' SQL SECURITY DEFINER
VIEW stillwater.briefing_teams AS
SELECT team_id, source_team_id, name FROM stillwater.teams;

CREATE DEFINER='stillwater_view_owner'@'localhost' SQL SECURITY DEFINER
VIEW stillwater.briefing_games AS
SELECT g.game_id, g.source_game_id, g.season, g.season_type, g.start_time_utc,
       g.home_team_id, g.away_team_id, g.home_points, g.away_points,
       g.neutral_site, g.venue, r.source, r.endpoint,
       r.source_retrieved_at_utc, r.response_sha256
FROM stillwater.games AS g
JOIN stillwater.ingestion_runs AS r ON r.ingestion_run_id=g.ingestion_run_id;

CREATE DEFINER='stillwater_view_owner'@'localhost' SQL SECURITY DEFINER
VIEW stillwater.briefing_team_game_stats AS
SELECT s.game_id, s.team_id, s.first_downs, s.total_yards, s.passing_yards,
       s.rushing_yards, s.rushing_attempts, s.pass_completions, s.pass_attempts,
       s.third_down_conversions, s.third_down_attempts,
       s.fourth_down_conversions, s.fourth_down_attempts,
       s.penalty_count, s.penalty_yards, s.interceptions_thrown, s.fumbles_lost,
       s.turnovers, s.possession_seconds, r.source, r.endpoint,
       r.source_retrieved_at_utc, r.response_sha256
FROM stillwater.team_game_stats AS s
JOIN stillwater.ingestion_runs AS r ON r.ingestion_run_id=s.ingestion_run_id;

GRANT SELECT ON stillwater.briefing_teams TO 'stillwater_mcp'@'%';
GRANT SELECT ON stillwater.briefing_games TO 'stillwater_mcp'@'%';
GRANT SELECT ON stillwater.briefing_team_game_stats TO 'stillwater_mcp'@'%';

-- Harmless private fixture, deliberately excluded from all MCP/definer grants.
CREATE TABLE stillwater.private_security_fixture (
    fixture_id INT PRIMARY KEY,
    note VARCHAR(128) NOT NULL
) ENGINE=InnoDB;
INSERT INTO stillwater.private_security_fixture VALUES (1, 'Harmless private test record');
