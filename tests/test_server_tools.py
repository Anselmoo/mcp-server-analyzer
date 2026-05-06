from mcp_server_analyzer import server


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

    from typing import Any, cast

    ruff_check_fn = cast(Any, server.ruff_check).fn
    res = ruff_check_fn("x=1")
    assert "total_issues" in res

    ruff_format_fn = cast(Any, server.ruff_format).fn
    res_fmt = ruff_format_fn("x=1")
    assert "formatted_code" in res_fmt or "total_issues" in res_fmt

    ruff_ci_fn = cast(Any, server.ruff_check_ci).fn
    res_ci = ruff_ci_fn("x=1")
    assert res_ci.get("success") is True


def test_analyze_code_with_missing_analyzers(monkeypatch):
    # ruff present, ty and vulture absent
    fake = FakeRuffAnalyzer()
    monkeypatch.setattr(server, "ruff_analyzer", fake)
    monkeypatch.setattr(server, "ruff_available", True)
    monkeypatch.setattr(server, "ty_available", False)
    monkeypatch.setattr(server, "vulture_available", False)

    from typing import Any, cast

    analyze_fn = cast(Any, server.analyze_code).fn
    result = analyze_fn("x=1")
    assert "summary" in result
    assert result["summary"]["total_ruff_issues"] == 0
