"""Build the .mcpb release bundle for mcp-server-analyzer.

Creates dist/mcp-server-analyzer-{version}.mcpb — a ZIP archive containing:
  manifest.json     DXT spec v0.4 manifest
  server/main.py    stdlib-only uvx launcher shim (DXT entry_point)

Deliberately does NOT bundle pyproject.toml: including it at archive root
triggers Claude Desktop's build_editable path, which fails because the
full source tree is absent.  The shim + mcp_config.command=uv is the
correct pattern for PyPI-distributed uv servers.
"""

from __future__ import annotations

import json
import textwrap
import tomllib
import zipfile
from pathlib import Path


def _read_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as fh:
        data = tomllib.load(fh)
    return data["project"]["version"]


def _build_manifest(version: str) -> dict:
    return {
        "manifest_version": "0.4",
        "name": "mcp-server-analyzer",
        "display_name": "MCP Server Analyzer",
        "version": version,
        "description": (
            "MCP server for Python code analysis with Ruff linting, "
            "ty type checking, and Vulture dead code detection."
        ),
        "author": {
            "name": "Anselm Hahn",
            "email": "anselm.hahn@gmail.com",
            "url": "https://github.com/anselmoo/mcp-server-analyzer",
        },
        "repository": {
            "type": "git",
            "url": "https://github.com/anselmoo/mcp-server-analyzer",
        },
        "documentation": "https://github.com/anselmoo/mcp-server-analyzer",
        "license": "MIT",
        "keywords": [
            "mcp",
            "ruff",
            "ty",
            "vulture",
            "code-analysis",
            "python",
        ],
        "server": {
            "type": "uv",
            "entry_point": "server/main.py",
            "mcp_config": {
                "command": "uv",
                "args": [
                    "tool",
                    "run",
                    "--from",
                    f"mcp-server-analyzer=={version}",
                    "mcp-server-analyzer",
                ],
            },
        },
        "tools_generated": True,
        "compatibility": {
            "claude_desktop": ">=0.10.0",
            "platforms": ["darwin", "win32", "linux"],
            "runtimes": {"python": ">=3.13"},
        },
    }


def _build_shim(version: str) -> str:
    """Return a stdlib-only launcher shim with the version baked in."""
    return textwrap.dedent(f"""\
        \"\"\"MCP Server Analyzer — uvx launcher shim.

        Serves as the DXT entry_point.  The preferred launch path is
        mcp_config.command (uv tool run) declared in manifest.json; this file
        acts as a direct fallback when run via ``uv run server/main.py``.
        \"\"\"

        from __future__ import annotations

        import os

        _PACKAGE = "mcp-server-analyzer"
        _VERSION = "{version}"
        _ENTRYPOINT = "mcp-server-analyzer"


        def main() -> None:
            os.execvp(
                "uv",
                ["uv", "tool", "run", "--from", f"{{_PACKAGE}}=={{_VERSION}}", _ENTRYPOINT],
            )


        if __name__ == "__main__":
            main()
        """)


def main() -> None:
    root = Path(__file__).parent.parent
    version = _read_version(root)
    manifest = _build_manifest(version)
    shim = _build_shim(version)

    dist = root / "dist"
    dist.mkdir(exist_ok=True)

    mcpb_path = dist / f"mcp-server-analyzer-{version}.mcpb"
    with zipfile.ZipFile(mcpb_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("server/main.py", shim)

    print(f"Built {mcpb_path}")


if __name__ == "__main__":
    main()
