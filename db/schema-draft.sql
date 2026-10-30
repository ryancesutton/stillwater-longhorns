-- Reviewed initial schema: applied to local Docker MySQL 8.4.13.
-- Not yet a versioned migration. CREATE statements are not rerunnable as-is.
-- Target: MySQL 8.4. Do not use on the
-- existing MySQL 5.7 installation: CHECK enforcement must be verified.
-- Run eventually with the migration identity against the chosen project DB.
-- No CREATE DATABASE, users, grants, secrets, or destructive statements here.
-- All *_utc DATETIME values are UTC by application convention.

CREATE TABLE ingestion_runs (
    ingestion_run_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source VARCHAR(32) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_parameters JSON NOT NULL,
    source_retrieved_at_utc DATETIME(6) NOT NULL,
    response_sha256 CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    -- Relative to the private archive root; never a credential-bearing URL.
    raw_file_path VARCHAR(512) NOT NULL,
    -- NULL means unknown; dirty flag NULL means Git state unavailable.
    importer_version VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL,
    importer_worktree_dirty BOOLEAN NULL,
    started_at_utc DATETIME(6) NOT NULL,
    finished_at_utc DATETIME(6) NULL,
    status VARCHAR(16) NOT NULL,
    records_processed INT UNSIGNED NOT NULL DEFAULT 0,
    error_summary VARCHAR(512) NULL,
    PRIMARY KEY (ingestion_run_id),
    CONSTRAINT ck_run_status CHECK (status IN ('running', 'succeeded', 'failed')),
    CONSTRAINT ck_run_finish CHECK (
        (status = 'running' AND finished_at_utc IS NULL) OR
        (status IN ('succeeded', 'failed') AND finished_at_utc IS NOT NULL)
    ),
    CONSTRAINT ck_run_times CHECK (finished_at_utc >= started_at_utc),
    CONSTRAINT ck_run_dirty CHECK (importer_worktree_dirty IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE teams (
    team_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_team_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(128) NOT NULL,
    -- Latest successful import that created or refreshed this identity.
    ingestion_run_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (team_id),
    UNIQUE KEY uq_team_source (source_team_id),
    CONSTRAINT fk_team_run FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE games (
    game_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    source_game_id BIGINT UNSIGNED NOT NULL,
    season SMALLINT UNSIGNED NOT NULL,
    season_type VARCHAR(32) NOT NULL,
    start_time_utc DATETIME(3) NOT NULL,
    home_team_id BIGINT UNSIGNED NOT NULL,
    away_team_id BIGINT UNSIGNED NOT NULL,
    home_points SMALLINT UNSIGNED NOT NULL,
    away_points SMALLINT UNSIGNED NOT NULL,
    neutral_site BOOLEAN NOT NULL,
    venue VARCHAR(255) NULL,
    ingestion_run_id BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (game_id),
    UNIQUE KEY uq_game_source (source_game_id),
    KEY ix_game_season_time (season, start_time_utc),
    CONSTRAINT fk_game_home FOREIGN KEY (home_team_id) REFERENCES teams (team_id),
    CONSTRAINT fk_game_away FOREIGN KEY (away_team_id) REFERENCES teams (team_id),
    CONSTRAINT fk_game_run FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id),
    CONSTRAINT ck_game_teams CHECK (home_team_id <> away_team_id),
    CONSTRAINT ck_game_type CHECK (season_type IN ('regular', 'postseason')),
    CONSTRAINT ck_game_neutral CHECK (neutral_site IN (0, 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE team_game_stats (
    game_id BIGINT UNSIGNED NOT NULL,
    team_id BIGINT UNSIGNED NOT NULL,
    ingestion_run_id BIGINT UNSIGNED NOT NULL,
    -- NULL means unavailable; zero is an actual reported value.
    first_downs SMALLINT UNSIGNED NULL,
    total_yards INT NULL,
    passing_yards INT NULL,
    rushing_yards INT NULL,
    rushing_attempts SMALLINT UNSIGNED NULL,
    pass_completions SMALLINT UNSIGNED NULL,
    pass_attempts SMALLINT UNSIGNED NULL,
    third_down_conversions SMALLINT UNSIGNED NULL,
    third_down_attempts SMALLINT UNSIGNED NULL,
    fourth_down_conversions SMALLINT UNSIGNED NULL,
    fourth_down_attempts SMALLINT UNSIGNED NULL,
    penalty_count SMALLINT UNSIGNED NULL,
    penalty_yards SMALLINT UNSIGNED NULL,
    interceptions_thrown SMALLINT UNSIGNED NULL,
    fumbles_lost SMALLINT UNSIGNED NULL,
    turnovers SMALLINT UNSIGNED NULL,
    possession_seconds INT UNSIGNED NULL,
    PRIMARY KEY (game_id, team_id),
    CONSTRAINT fk_stats_game FOREIGN KEY (game_id) REFERENCES games (game_id),
    CONSTRAINT fk_stats_team FOREIGN KEY (team_id) REFERENCES teams (team_id),
    CONSTRAINT fk_stats_run FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id),
    CONSTRAINT ck_stats_pass CHECK (pass_completions <= pass_attempts),
    CONSTRAINT ck_stats_third CHECK (third_down_conversions <= third_down_attempts),
    CONSTRAINT ck_stats_fourth CHECK (fourth_down_conversions <= fourth_down_attempts),
    CONSTRAINT ck_stats_yards CHECK (total_yards = passing_yards + rushing_yards),
    CONSTRAINT ck_stats_turnovers CHECK (turnovers = interceptions_thrown + fumbles_lost)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Importer must additionally verify that each stats team is one of the game's
-- participants. Separate foreign keys above do not enforce that relationship.
-- Scope is completed historical games; upcoming games need a future migration
-- for completion state and nullable scores. Source IDs refer only to CFBD.
-- One run covers one saved response. Reimports create new run records but
-- update dataset rows using unique source IDs / the composite stats key.
-- Commit a running run first; commit dataset changes and success together.
-- On failure roll back dataset changes, then mark the run failed separately.
-- Run metadata is importer-controlled provenance, not tamper-proof audit data.
-- Approved MCP views and least-privilege grants require a separate review.
