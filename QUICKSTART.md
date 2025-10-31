# Quick Start Guide

## 🚀 One-Line Install

### Option 1: Run from GitHub (once published)

```bash
nix run github:yourusername/nixpkgs-mcp
```

### Option 2: Run from Local Repo

```bash
nix run /home/lessuseless/Projects/nixpkgs-mcp
```

### Option 3: Add to Your MCP Configuration

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
      "args": ["run", "/home/lessuseless/Projects/nixpkgs-mcp"],
      "env": {}
    }
  }
}
```

That's it! Restart your MCP client (Claude Code, etc.) and the server will be available.

## 🧪 Testing (Optional)

If you want to test before using:

```bash
nix develop /home/lessuseless/Projects/nixpkgs-mcp
python3 test_server.py
```

## 🎯 Try It Out!

In your AI agent (Claude, etc.), try these commands:

**Search for packages:**
```
Use nixpkgs_search to find file searching tools
```

**Execute a package once:**
```
Use nixpkgs_execute to run ripgrep with args ["TODO", "."]
```

**Install a tool permanently:**
```
Use nixpkgs_install_tool to register nushell
```

**Use installed tools:**
```
Use nixpkgs_nushell with args ["script.nu"]
```

## 📋 Available Meta Tools

| Tool | Description | Example |
|------|-------------|---------|
| `nixpkgs_search` | Find packages | `{"query": "json parser", "limit": 10}` |
| `nixpkgs_execute` | Run any package | `{"package": "jq", "args": [".name"]}` |
| `nixpkgs_install_tool` | Register tool | `{"package": "ripgrep"}` |
| `nixpkgs_list_installed` | Show tools | `{}` |

## 🔧 Pre-installed Tools

Already available without search:
- `nixpkgs_ripgrep` - Fast recursive search
- `nixpkgs_jq` - JSON processor
- `nixpkgs_fd` - User-friendly find
- `nixpkgs_bat` - Cat clone with syntax highlighting
- `nixpkgs_eza` - Modern ls replacement
- `nixpkgs_fzf` - Fuzzy finder
- `nixpkgs_git` - Version control
- `nixpkgs_curl` - HTTP client
- `nixpkgs_htop` - Process viewer
- `nixpkgs_nushell` - Modern shell

## 🐛 Troubleshooting

### "Package not found"
```bash
# Update cache
rm -rf ~/.cache/nixpkgs-mcp
python3 server.py  # Will re-download metadata
```

### "Command timed out"
Some packages take longer to run. Edit `server.py` and increase timeout:
```python
timeout=30  # Change to 60 or more
```

### "Nix not found"
Make sure nix is in your PATH:
```bash
which nix
# If not found:
export PATH="/nix/var/nix/profiles/default/bin:$PATH"
```

## 🎯 Next Steps

1. **Read ARCHITECTURE.md** - Understand the design
2. **Star the repo** - Help others discover it
3. **Contribute** - See roadmap in README.md
4. **Report issues** - Open GitHub issues

## 🔄 Updating

```bash
# Pull latest changes
git pull

# Clear cache to get fresh package list
rm -rf ~/.cache/nixpkgs-mcp

# Restart server
```

## 🌟 Pro Tips

**Tip 1: Batch Install**
Install multiple tools at once by calling `nixpkgs_install_tool` repeatedly:
```
Install these tools: ripgrep, jq, fd, bat, nushell
```

**Tip 2: Explore Categories**
Search by category:
```
Search nixpkgs for: python data analysis tools
Search nixpkgs for: rust CLI tools
Search nixpkgs for: network monitoring utilities
```

**Tip 3: Check Versions**
Package metadata includes versions:
```
Search for nodejs and show versions
```

**Tip 4: Combine with Other MCP Servers**
Use alongside mcp-nixos for NixOS configuration info:
- This server: Run nixpkgs packages
- mcp-nixos: Query NixOS options and packages

## 📚 Learning Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Nixpkgs Manual](https://nixos.org/manual/nixpkgs/stable/)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)

---

**Need Help?** Open an issue on GitHub or ask your AI assistant to debug!
