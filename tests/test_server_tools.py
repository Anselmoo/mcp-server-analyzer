from mcp_server_analyzer import server
from mcp_server_analyzer.models import (
    ActionlintCheckResult,
    AnalysisResult,
    BiomeCheckResult,
    BiomeFormatResult,
    GitleaksScanResult,
    RuffCheckResult,
    RuffCICheckResult,
    SemgrepScanResult,
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


class FakeBiomeAnalyzer:
    def check_code(self, code, filename="code.ts"):
        return BiomeCheckResult(issues=[], total_issues=0, errors=0, warnings=0)

    def format_code(self, code, filename="code.ts"):
        return BiomeFormatResult(formatted_code=code, changed=False)


def test_server_biome_wrappers(monkeypatch):
    fake = FakeBiomeAnalyzer()
    monkeypatch.setattr(server, "biome_analyzer", fake)
    monkeypatch.setattr(server, "biome_available", True)

    res = _get_fn(server.biome_check)("const x = 1;\n")
    assert isinstance(res, BiomeCheckResult)
    assert res.total_issues == 0

    res_fmt = _get_fn(server.biome_format)("const x = 1;\n")
    assert isinstance(res_fmt, BiomeFormatResult)
    assert res_fmt.changed is False


class FakeSemgrepAnalyzer:
    def check_code(self, code, config="auto", filename="code.py"):
        return SemgrepScanResult(
            issues=[], total_issues=0, error_count=0, warning_count=0
        )


def test_server_semgrep_wrappers(monkeypatch):
    fake = FakeSemgrepAnalyzer()
    monkeypatch.setattr(server, "semgrep_analyzer", fake)
    monkeypatch.setattr(server, "semgrep_available", True)

    res = _get_fn(server.semgrep_check)("x = 1\n")
    assert isinstance(res, SemgrepScanResult)
    assert res.total_issues == 0


class FakeActionlintAnalyzer:
    def check_workflow(self, code, filename="workflow.yml"):
        return ActionlintCheckResult(issues=[], total_issues=0)


def test_server_actionlint_wrappers(monkeypatch):
    fake = FakeActionlintAnalyzer()
    monkeypatch.setattr(server, "actionlint_analyzer", fake)
    monkeypatch.setattr(server, "actionlint_available", True)

    res = _get_fn(server.actionlint_check)("on: push\n")
    assert isinstance(res, ActionlintCheckResult)
    assert res.total_issues == 0


class FakeGitleaksAnalyzer:
    def scan_code(self, code, filename="code.txt"):
        return GitleaksScanResult(findings=[], total_findings=0)


def test_server_gitleaks_wrappers(monkeypatch):
    fake = FakeGitleaksAnalyzer()
    monkeypatch.setattr(server, "gitleaks_analyzer", fake)
    monkeypatch.setattr(server, "gitleaks_available", True)

    res = _get_fn(server.gitleaks_scan)("hello world\n")
    assert isinstance(res, GitleaksScanResult)
    assert res.total_findings == 0


def test_analyze_code_with_missing_analyzers(monkeypatch):
    fake = FakeRuffAnalyzer()
    monkeypatch.setattr(server, "ruff_analyzer", fake)
    monkeypatch.setattr(server, "ruff_available", True)
    monkeypatch.setattr(server, "ty_available", False)
    monkeypatch.setattr(server, "vulture_available", False)

    result = _get_fn(server.analyze_code)("x=1")
    assert isinstance(result, AnalysisResult)
    assert result.summary.total_ruff_issues == 0
