from pathlib import Path

from omnicli.portfolio import PortfolioContext


def test_portfolio_context_has_stable_fingerprint(tmp_path: Path) -> None:
    path = tmp_path / "capabilities.yaml"
    path.write_text("version: 1\ncapabilities: {}\n", encoding="utf-8")
    first = PortfolioContext.from_file(path)
    second = PortfolioContext.from_file(path)
    assert first.fingerprint == second.fingerprint
    assert "sha256=" in first.prompt_text()
