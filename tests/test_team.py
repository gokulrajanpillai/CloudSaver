from cloudsaver.history import connect_history


def table_names(connection):
    return {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }


def test_team_schema_tables_created(tmp_path):
    with connect_history(tmp_path / "history.sqlite3") as connection:
        names = table_names(connection)

    assert "team_workspaces" in names
    assert "team_members" in names
    assert "shared_audits" in names
    assert "scheduled_scans" in names
