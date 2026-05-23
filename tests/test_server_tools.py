from mcp_server_analyzer import server
from mcp_server_analyzer.models import (
    AnalysisResult,
    RuffCheckResult,
    RuffCICheckResult,
)


def _get_fn(tool):
    return getattr(tool, "fn", tool)


class FakeRuffAnalyzer:
    def check_code(self, *_args, **_kwargs):
        return RuffCheckResult(issues=[], total_issues=0, fixable_issues=0)

    def format_code(self, code, *_args, **_kwargs):
        from mcp_server_analyzer.models import RuffFormatResult

        return RuffFormatResult(formatted_code=code, changed=False)

    def check_code_for_ci(self, *_args, **_kwargs):
        return "RAW_OUTPUT"


def test_server_ruff_wrappers(monkeypatch):
    fake = FakeRuffAnalyzer()
    monkeypatch.setattr(server, "ruff_analyzer", fake)
    monkeypatch.setattr(server, "ruff_available", True)

    res = _get_fn(server.ruff_check)("x=1")
    assert isinstance(res, RuffCheckResult)
    assert res.total_issues == 0

    res_fmt = _get_fn(server.ruff_format)("x=1")
    assert hasattr(res_fmt, "formatted_code")

    res_ci = _get_fn(server.ruff_check_ci)("x=1")
    assert isinstance(res_ci, RuffCICheckResult)
    assert res_ci.success is True


def test_analyze_code_with_missing_analyzers(monkeypatch):
    fake = FakeRuffAnalyzer()
    monkeypatch.setattr(server, "ruff_analyzer", fake)
    monkeypatch.setattr(server, "ruff_available", True)
    monkeypatch.setattr(server, "ty_available", False)
    monkeypatch.setattr(server, "vulture_available", False)

    result = _get_fn(server.analyze_code)("x=1")
    assert isinstance(result, AnalysisResult)
    assert result.summary.total_ruff_issues == 0
