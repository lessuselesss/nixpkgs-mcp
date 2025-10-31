#!/usr/bin/env python3
"""
Quick test script to verify the MCP server works
"""

import asyncio
import json


async def test_server():
    """Basic functionality tests"""
    from server import NixpkgsMCPServer

    print("🧪 Testing Nixpkgs MCP Server\n")

    server = NixpkgsMCPServer()

    # Test 1: Load metadata
    print("1️⃣  Loading nixpkgs metadata...")
    await server.load_nixpkgs_metadata()
    assert len(server.packages) > 1000, "Should load thousands of packages"
    print(f"   ✅ Loaded {len(server.packages)} packages\n")

    # Test 2: List tools
    print("2️⃣  Listing available tools...")
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]
    assert "nixpkgs_search" in tool_names, "Should have search tool"
    assert "nixpkgs_execute" in tool_names, "Should have execute tool"
    assert "nixpkgs_ripgrep" in tool_names, "Should have ripgrep pre-registered"
    print(f"   ✅ Found {len(tools)} tools (4 meta + {len(server.installed_tools)} packages)\n")

    # Test 3: Search packages
    print("3️⃣  Testing package search...")
    results = await server.search_packages("json", 5)
    assert len(results) > 0, "Should find json-related packages"
    print(f"   ✅ Search works\n")

    # Test 4: Install tool
    print("4️⃣  Testing tool installation...")
    initial_count = len(server.installed_tools)
    result = await server.install_tool("nushell")
    assert "nushell" in server.installed_tools, "Should install nushell"
    assert len(server.installed_tools) == initial_count + 1, "Tool count should increase"
    print(f"   ✅ Tool installation works\n")

    # Test 5: Execute package (echo test)
    print("5️⃣  Testing package execution...")
    result = await server.execute_package("hello", ["--version"], None)
    assert len(result) > 0, "Should return output"
    print(f"   ✅ Package execution works\n")

    print("🎉 All tests passed!")
    print("\nNext steps:")
    print("  1. Add to .mcp.json (already done)")
    print("  2. Restart Claude Code or run: claude mcp reload")
    print("  3. Try: 'Use nixpkgs_search to find ripgrep'")


if __name__ == "__main__":
    asyncio.run(test_server())
