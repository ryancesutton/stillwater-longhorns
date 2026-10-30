-- Runtime importer only: no schema administration, DELETE, or grant option.
GRANT SELECT, INSERT, UPDATE ON stillwater.teams TO 'stillwater_import'@'%';
GRANT SELECT, INSERT, UPDATE ON stillwater.games TO 'stillwater_import'@'%';
GRANT SELECT, INSERT, UPDATE ON stillwater.team_game_stats TO 'stillwater_import'@'%';
GRANT SELECT, INSERT, UPDATE ON stillwater.ingestion_runs TO 'stillwater_import'@'%';
