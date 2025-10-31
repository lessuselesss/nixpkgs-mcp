#!/usr/bin/env python3
"""
Nixpkgs MCP Server - Dynamic tool generation for all nixpkgs packages
Supports lazy loading of 80,000+ packages with intelligent caching
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.request import urlopen

from mcp.server import Server
from mcp.types import Tool, TextContent


class NixpkgsMCPServer:
    """MCP server that dynamically exposes nixpkgs packages as tools"""

    def __init__(self):
        self.server = Server("nixpkgs-mcp")
        self.packages: dict[str, dict] = {}
        self.installed_tools: set[str] = set()
        self.common_tools = {
            "ripgrep", "jq", "fd", "bat", "eza", "fzf", "git",
            "curl", "wget", "htop", "tree", "nushell"
        }

        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    async def load_nixpkgs_metadata(self):
        """Load package metadata from nixpkgs.json"""
        cache_file = Path.home() / ".cache/nixpkgs-mcp/nixpkgs.json"

        if cache_file.exists():
            print("Loading cached nixpkgs metadata...", file=sys.stderr)
            with open(cache_file) as f:
                data = json.load(f)
        else:
            print("Downloading nixpkgs metadata...", file=sys.stderr)
            url = "https://raw.githubusercontent.com/pkgforge-dev/NixOS-Packages/refs/heads/main/nixpkgs.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            with urlopen(url) as response:
                data = json.loads(response.read())

            with open(cache_file, 'w') as f:
                json.dump(data, f)

        # Parse package data - extract pname from key
        for key, info in data.items():
            # key format: "legacyPackages.x86_64-linux.PACKAGE_NAME"
            parts = key.split(".")
            if len(parts) >= 3:
                pkg_name = parts[-1]
                self.packages[pkg_name] = {
                    "pname": info.get("pname", pkg_name),
                    "description": info.get("description", ""),
                    "version": info.get("version", ""),
                }

        # Pre-install common tools
        self.installed_tools.update(self.common_tools)

        print(f"Loaded {len(self.packages)} packages", file=sys.stderr)
        print(f"Pre-registered {len(self.installed_tools)} common tools", file=sys.stderr)

    def create_tool_definition(self, pkg_name: str) -> Tool:
        """Generate MCP tool definition for a nixpkgs package"""
        pkg_info = self.packages.get(pkg_name, {})
        description = pkg_info.get("description", f"Run {pkg_name} from nixpkgs")

        return Tool(
            name=f"nixpkgs_{pkg_name.replace('-', '_')}",
            description=f"{description}\nVersion: {pkg_info.get('version', 'unknown')}",
            inputSchema={
                "type": "object",
                "properties": {
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Command-line arguments to pass to the tool"
                    },
                    "stdin": {
                        "type": "string",
                        "description": "Optional input to pass via stdin"
                    }
                },
                "required": []
            }
        )

    async def list_tools(self) -> list[Tool]:
        """Return list of available tools"""
        tools = [
            # Meta tools
            Tool(
                name="nixpkgs_search",
                description="Search for packages in nixpkgs by name or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (package name or keywords)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 20)",
                            "default": 20
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="nixpkgs_execute",
                description="Execute any nixpkgs package once without registering as a tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package": {
                            "type": "string",
                            "description": "Package name from nixpkgs"
                        },
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Command-line arguments"
                        },
                        "stdin": {
                            "type": "string",
                            "description": "Optional stdin input"
                        }
                    },
                    "required": ["package"]
                }
            ),
            Tool(
                name="nixpkgs_install_tool",
                description="Permanently register a nixpkgs package as an MCP tool for future use",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "package": {
                            "type": "string",
                            "description": "Package name to register as a tool"
                        }
                    },
                    "required": ["package"]
                }
            ),
            Tool(
                name="nixpkgs_list_installed",
                description="List all currently installed/registered nixpkgs tools",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
        ]

        # Add installed tool definitions
        for pkg_name in sorted(self.installed_tools):
            if pkg_name in self.packages:
                tools.append(self.create_tool_definition(pkg_name))

        return tools

    async def call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool"""

        # Meta tools
        if name == "nixpkgs_search":
            return await self.search_packages(arguments["query"], arguments.get("limit", 20))

        elif name == "nixpkgs_execute":
            return await self.execute_package(
                arguments["package"],
                arguments.get("args", []),
                arguments.get("stdin")
            )

        elif name == "nixpkgs_install_tool":
            return await self.install_tool(arguments["package"])

        elif name == "nixpkgs_list_installed":
            installed = sorted(self.installed_tools)
            return [TextContent(
                type="text",
                text=f"Installed nixpkgs tools ({len(installed)}):\n" +
                     "\n".join(f"  - {pkg}" for pkg in installed)
            )]

        # Installed package tools
        elif name.startswith("nixpkgs_"):
            pkg_name = name[8:].replace("_", "-")  # Remove nixpkgs_ prefix
            return await self.execute_package(
                pkg_name,
                arguments.get("args", []),
                arguments.get("stdin")
            )

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def search_packages(self, query: str, limit: int) -> list[TextContent]:
        """Search for packages matching query"""
        query_lower = query.lower()
        results = []

        for pkg_name, info in self.packages.items():
            if (query_lower in pkg_name.lower() or
                query_lower in info.get("description", "").lower()):
                results.append({
                    "name": pkg_name,
                    "description": info.get("description", ""),
                    "version": info.get("version", ""),
                    "installed": pkg_name in self.installed_tools
                })

                if len(results) >= limit:
                    break

        if not results:
            return [TextContent(
                type="text",
                text=f"No packages found matching '{query}'"
            )]

        output = f"Found {len(results)} packages matching '{query}':\n\n"
        for r in results:
            installed = " [INSTALLED]" if r["installed"] else ""
            output += f"📦 {r['name']} (v{r['version']}){installed}\n"
            output += f"   {r['description']}\n\n"

        return [TextContent(type="text", text=output)]

    async def install_tool(self, package: str) -> list[TextContent]:
        """Register a package as a permanent tool"""
        if package not in self.packages:
            return [TextContent(
                type="text",
                text=f"❌ Package '{package}' not found in nixpkgs"
            )]

        if package in self.installed_tools:
            return [TextContent(
                type="text",
                text=f"ℹ️  Package '{package}' is already installed as a tool"
            )]

        self.installed_tools.add(package)

        # Send notification to client that tools have changed
        # Note: This requires MCP protocol support for notifications

        return [TextContent(
            type="text",
            text=f"✅ Installed '{package}' as tool: nixpkgs_{package.replace('-', '_')}\n" +
                 f"You can now call it directly without using nixpkgs_execute."
        )]

    async def execute_package(
        self,
        package: str,
        args: list[str],
        stdin: Optional[str] = None
    ) -> list[TextContent]:
        """Execute a nixpkgs package"""

        if package not in self.packages:
            return [TextContent(
                type="text",
                text=f"❌ Package '{package}' not found in nixpkgs. Use nixpkgs_search to find it."
            )]

        cmd = ["nix", "run", f"nixpkgs#{package}", "--"] + args

        try:
            result = subprocess.run(
                cmd,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = ""
            if result.stdout:
                output += f"📤 stdout:\n{result.stdout}\n"
            if result.stderr:
                output += f"⚠️  stderr:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"\n❌ Exit code: {result.returncode}"
            else:
                output += f"\n✅ Success (exit code: 0)"

            return [TextContent(type="text", text=output)]

        except subprocess.TimeoutExpired:
            return [TextContent(
                type="text",
                text=f"❌ Command timed out after 30 seconds"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error executing package: {str(e)}"
            )]

    async def run(self):
        """Start the MCP server"""
        await self.load_nixpkgs_metadata()

        # Run server with stdio transport
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def async_main():
    server = NixpkgsMCPServer()
    await server.run()


def main():
    """Entry point for console_scripts"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
