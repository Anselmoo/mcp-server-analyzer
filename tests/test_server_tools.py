from mcp_server_analyzer import server


def _get_fn(tool):
    return getattr(tool, "fn", tool)


class FakeRuffResult:
    def __init__(self):
        self.total_issues = 0
        self.fixable_issues = 0
        self.issues = []

    def model_dump(self):
        return {
            "issues": [],
            "total_issues": self.total_issues,
            "fixable_issues": self.fixable_issues,
        }


class FakeRuffAnalyzer:
    def check_code(self, *_args, **_kwargs):
        return FakeRuffResult()

    def format_code(self, *_args, **_kwargs):
        return FakeRuffResult()

    def check_code_for_ci(self, *_args, **_kwargs):
        return "RAW_OUTPUT"


def test_server_ruff_wrappers(monkeypatch):
    # Install fake analyzer
    fake = FakeRuffAnalyzer()
    monkeypatch.setattr(server, "ruff_analyzer", fake)
    monkeypatch.setattr(server, "ruff_available", True)

    res = _get_fn(server.ruff_check)("x=1")
    assert "total_issues" in res

    res_fmt = _get_fn(server.ruff_format)("x=1")
    assert "formatted_code" in res_fmt or "total_issues" in res_fmt

    res_ci = _get_fn(server.ruff_check_ci)("x=1")
    assert res_ci.get("success") is True


def test_analyze_code_with_missing_analyzers(monkeypatch):
    # ruff present, ty and vulture absent
    fake = FakeRuffAnalyzer()
    monkeypatch.setattr(server, "ruff_analyzer", fake)
    monkeypatch.setattr(server, "ruff_available", True)
    monkeypatch.setattr(server, "ty_available", False)
    monkeypatch.setattr(server, "vulture_available", False)

    result = _get_fn(server.analyze_code)("x=1")
    assert "summary" in result
    assert result["summary"]["total_ruff_issues"] == 0
