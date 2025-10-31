# Nixpkgs MCP Server

**Dynamic MCP server that exposes all 80,000+ nixpkgs packages as tools to AI agents.**

## Features

- 🚀 **Dynamic Tool Generation**: Access any nixpkgs package on-demand
- ⚡ **Lazy Loading**: Fast startup with incremental tool registration
- 🔍 **Intelligent Search**: Find packages by name or description
- 💾 **Smart Caching**: Pre-register common tools, load others as needed
- 🛠️ **Three-Tier System**:
  - Meta tools (search, execute, install)
  - Pre-registered common tools (ripgrep, jq, fd, etc.)
  - On-demand dynamic tools (80k+ packages)

## Quick Start

### One-Line Install

```bash
# Run from GitHub (once published)
nix run github:yourusername/nixpkgs-mcp

# Or run from local clone
nix run /path/to/nixpkgs-mcp
```

### Add to MCP Configuration

Add to `~/.mcp.json` or your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "nixpkgs": {
      "command": "nix",
      "args": ["run", "github:yourusername/nixpkgs-mcp"],
      "env": {}
    }
  }
}
```

Or for local development:

```json
{
  "mcpServers": {
    "nixpkgs": {
      "command": "nix",
      "args": ["run", "/path/to/nixpkgs-mcp"],
      "env": {}
    }
  }
}
```

Restart your MCP client and start using nixpkgs tools!

## Usage Examples

### Search for packages

```
Agent: Use nixpkgs_search to find JSON processing tools
```

### Execute a package once

```
Agent: Use nixpkgs_execute to run jq with args [".name", "-"]
```

### Install a tool permanently

```
Agent: Use nixpkgs_install_tool to register nushell
```

Now `nixpkgs_nushell` is available as a direct tool!

### Use pre-registered tools

```
Agent: Use nixpkgs_ripgrep with args ["--json", "TODO", "."]
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         MCP Client (Claude, etc)            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Nixpkgs MCP Server                  │
│  ┌────────────┐ ┌────────────┐ ┌──────────┐│
│  │Meta Tools  │ │Common Tools│ │ Dynamic  ││
│  │• search    │ │• ripgrep   │ │• 80k pkg ││
│  │• execute   │ │• jq        │ │• cached  ││
│  │• install   │ │• fd        │ │• on-dem  ││
│  └────────────┘ └────────────┘ └──────────┘│
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│   nix run nixpkgs#<package> -- <args>       │
└─────────────────────────────────────────────┘
```

## Available Meta Tools

| Tool | Description |
|------|-------------|
| `nixpkgs_search` | Search packages by name or description |
| `nixpkgs_execute` | Run any package without registering |
| `nixpkgs_install_tool` | Permanently register a package as a tool |
| `nixpkgs_list_installed` | Show all registered tools |

## Pre-registered Common Tools

- **Search**: ripgrep, fd, fzf
- **Data**: jq, nushell
- **Files**: bat, eza, tree
- **Network**: curl, wget
- **System**: htop, git

## Performance

- **Startup**: ~2s (loads 80k package metadata)
- **Search**: ~50ms (in-memory lookup)
- **Execute**: ~1-3s (nix run cold start) + tool runtime
- **Cached**: Sub-second for registered tools

## Caching Strategy

1. **Metadata Cache**: `~/.cache/nixpkgs-mcp/nixpkgs.json` (refreshed daily)
2. **Tool Registry**: In-memory set of installed tools
3. **Common Tools**: Pre-loaded at startup

## Development

```bash
# Enter dev environment
nix develop

# Run server
python server.py

# Test with MCP inspector
npx @modelcontextprotocol/inspector python server.py
```

## Roadmap

- [ ] Persistent tool registry (save installed tools to disk)
- [ ] Package metadata enrichment (maintainers, platforms, etc.)
- [ ] Smart tool suggestions based on context
- [ ] Batch tool registration
- [ ] Performance optimization (Go/Rust rewrite)
- [ ] Integration with mcp-nixos for NixOS-specific info
- [ ] Support for `nix shell` environments
- [ ] Tool usage analytics

## Related Projects

- [mcp-nixos](https://github.com/utensils/mcp-nixos) - MCP server for NixOS packages/options info
- [mcp-servers-nix](https://github.com/natsukium/mcp-servers-nix) - Nix framework for packaging MCP servers
- [NixOS-Packages](https://github.com/pkgforge-dev/NixOS-Packages) - Metadata source

## License

Unlicense - Public Domain
