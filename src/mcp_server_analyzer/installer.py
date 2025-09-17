"""Node.js dependency installer for MCP Server Analyzer."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class NodeJSInstaller:
    """Handles installation of Node.js dependencies for the MCP server."""

    def __init__(self, package_root: Optional[Path] = None):
        """Initialize the installer.
        
        Args:
            package_root: Root directory containing package.json
        """
        self.package_root = package_root or Path(__file__).parent.parent.parent.parent
        self.package_json = self.package_root / "package.json"

    def check_nodejs_available(self) -> bool:
        """Check if Node.js and npm are available on the system."""
        try:
            subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                check=True, 
                timeout=10
            )
            subprocess.run(
                ["npm", "--version"], 
                capture_output=True, 
                check=True, 
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install_dependencies(self, force: bool = False) -> bool:
        """Install Node.js dependencies from package.json.
        
        Args:
            force: Whether to force installation even if already installed
            
        Returns:
            True if installation was successful, False otherwise
        """
        if not self.check_nodejs_available():
            print(
                "Warning: Node.js and npm are required for JavaScript/TypeScript analysis features.",
                file=sys.stderr
            )
            print(
                "Please install Node.js from https://nodejs.org/ and run: npm install",
                file=sys.stderr
            )
            return False

        if not self.package_json.exists():
            print(f"Warning: package.json not found at {self.package_json}", file=sys.stderr)
            return False

        try:
            # Check if node_modules exists and has dependencies
            node_modules = self.package_root / "node_modules"
            if not force and node_modules.exists() and list(node_modules.iterdir()):
                # Dependencies likely already installed
                return True

            print("Installing Node.js dependencies...")
            subprocess.run(
                ["npm", "install"],
                cwd=self.package_root,
                check=True,
                timeout=120
            )
            print("Node.js dependencies installed successfully.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to install Node.js dependencies: {e}", file=sys.stderr)
            return False
        except subprocess.TimeoutExpired:
            print("Node.js dependency installation timed out.", file=sys.stderr)
            return False

    def check_tool_available(self, tool: str) -> bool:
        """Check if a specific Node.js tool is available.
        
        Args:
            tool: Name of the tool (e.g., 'biome', 'prettier')
            
        Returns:
            True if tool is available, False otherwise
        """
        try:
            subprocess.run(
                ["npx", tool, "--version"],
                capture_output=True,
                check=True,
                timeout=10,
                cwd=self.package_root
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Also try without specifying cwd in case the tool is globally available
            try:
                subprocess.run(
                    ["npx", tool, "--version"],
                    capture_output=True,
                    check=True,
                    timeout=10
                )
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return False

    def get_missing_tools(self, required_tools: List[str]) -> List[str]:
        """Get list of missing Node.js tools.
        
        Args:
            required_tools: List of tool names to check
            
        Returns:
            List of missing tool names
        """
        return [tool for tool in required_tools if not self.check_tool_available(tool)]

    def install_with_instructions(self) -> bool:
        """Install dependencies with user-friendly instructions.
        
        Returns:
            True if successful or user declined, False if error occurred
        """
        if not self.check_nodejs_available():
            print("\n" + "="*60)
            print("JavaScript/TypeScript Analysis Setup Required")
            print("="*60)
            print("This package provides advanced code analysis for JavaScript and TypeScript")
            print("using modern tools like Biome and Prettier, but requires Node.js.")
            print("\nTo enable JavaScript/TypeScript features:")
            print("1. Install Node.js from https://nodejs.org/")
            print("2. Run: npm install")
            print("3. Or use the Docker image which includes all dependencies")
            print("\nPython analysis features will continue to work without Node.js.")
            print("="*60 + "\n")
            return True

        return self.install_dependencies()


def ensure_nodejs_dependencies() -> bool:
    """Ensure Node.js dependencies are installed.
    
    This function can be called during package installation or at runtime
    to ensure all required Node.js tools are available.
    
    Returns:
        True if dependencies are available, False otherwise
    """
    installer = NodeJSInstaller()
    return installer.install_with_instructions()


if __name__ == "__main__":
    # Can be run as a standalone script
    installer = NodeJSInstaller()
    success = installer.install_with_instructions()
    sys.exit(0 if success else 1)