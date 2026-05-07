import runpy

from mcp_server_analyzer import server


def test_main_runs(monkeypatch):
    """Ensure server.main calls app.run without starting a real server."""
    monkeypatch.setattr(server.app, "run", lambda: None)
    # Should not raise
    server.main()


def test_package_entrypoint_runs(monkeypatch):
    """Run package as __main__ to exercise __main__.py entrypoint."""
    monkeypatch.setattr(server.app, "run", lambda: None)
    # run_module with run_name='__main__' will execute __main__.py
    runpy.run_module("mcp_server_analyzer", run_name="__main__")
