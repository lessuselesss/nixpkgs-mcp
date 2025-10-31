# Nixpkgs MCP Server Architecture

## Design Goals

1. **Universal Access**: Expose all 80,000+ nixpkgs packages to AI agents
2. **Efficiency**: Fast startup and low memory footprint
3. **Accuracy**: Correct package metadata and reliable execution
4. **Flexibility**: Support both one-off and persistent tool usage

## Three-Tier Tool Architecture

### Tier 1: Meta Tools (Always Available)

These are the core tools that enable discovery and management:

```
┌─────────────────────────────────────────────────────┐
│                   Meta Tools                        │
├─────────────────────────────────────────────────────┤
│ nixpkgs_search         Search by name/description   │
│ nixpkgs_execute        One-off package execution    │
│ nixpkgs_install_tool   Register package as tool     │
│ nixpkgs_list_installed Show registered tools        │
└─────────────────────────────────────────────────────┘
```

**Usage Pattern:**
1. Agent doesn't know what tools are available
2. Calls `nixpkgs_search("json parser")`
3. Finds `jq`, `jless`, `fx`, etc.
4. Calls `nixpkgs_execute("jq", [".name"])`
5. Or calls `nixpkgs_install_tool("jq")` for frequent use

### Tier 2: Pre-registered Common Tools (~100 tools)

Frequently-used packages are pre-registered at startup for immediate access:

```
┌─────────────────────────────────────────────────────┐
│               Common Tools (Pre-loaded)             │
├─────────────────────────────────────────────────────┤
│ Search/Filter    ripgrep, fd, fzf, eza              │
│ Data Processing  jq, nushell, miller                │
│ File Viewers     bat, tree, hexyl                   │
│ Network          curl, wget, httpie                 │
│ Development      git, gh, delta                     │
│ System           htop, bottom, procs                │
└─────────────────────────────────────────────────────┘
```

**Benefit**: Zero-latency access to common tools without search step.

### Tier 3: Dynamic Tools (80,000+ packages)

The full nixpkgs catalog is available on-demand:

```
┌─────────────────────────────────────────────────────┐
│          Dynamic Tools (On-Demand Loading)          │
├─────────────────────────────────────────────────────┤
│ 1. Agent requests package via install_tool          │
│ 2. Server validates package exists in metadata      │
│ 3. Tool definition generated dynamically            │
│ 4. Added to installed_tools set (in-memory)         │
│ 5. tools/list_changed notification sent (future)    │
│ 6. Tool available for subsequent calls              │
└─────────────────────────────────────────────────────┘
```

## Data Flow

### Startup Sequence

```
┌──────────────┐
│ Server Start │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Load Nixpkgs Metadata                │
│ • Check cache: ~/.cache/nixpkgs-mcp/ │
│ • Download if missing/stale          │
│ • Parse 80k+ package entries         │
│ • Build in-memory index              │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Pre-register Common Tools            │
│ • Add ~100 popular packages          │
│ • Generate tool definitions          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Start MCP Server (stdio)             │
│ • Listen for client connections      │
│ • Handle list_tools requests         │
│ • Handle call_tool requests          │
└──────────────────────────────────────┘
```

### Tool Execution Flow

**Scenario 1: Using Pre-registered Tool**

```
Agent: "Use ripgrep to search for 'TODO'"
  │
  ▼
┌─────────────────────────────────────────┐
│ MCP Client → call_tool("nixpkgs_ripgrep")│
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ Server: Extract args ["TODO", "."]      │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ Execute: nix run nixpkgs#ripgrep --     │
│          TODO .                         │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ Return stdout/stderr/exitcode          │
└─────────────────────────────────────────┘
```

**Scenario 2: Discovering and Installing New Tool**

```
Agent: "Find a better alternative to cat"
  │
  ▼
┌─────────────────────────────────────────┐
│ call_tool("nixpkgs_search",            │
│          {"query": "cat file viewer"})  │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ Search in-memory index                  │
│ Results: bat, glow, bat-extras          │
└─────────────────────────────────────────┘
  │
  ▼
Agent: "Install bat as a tool"
  │
  ▼
┌─────────────────────────────────────────┐
│ call_tool("nixpkgs_install_tool",      │
│          {"package": "bat"})            │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│ Add "bat" to installed_tools            │
│ Generate tool definition                │
│ Notify client (future: tools/changed)  │
└─────────────────────────────────────────┘
  │
  ▼
Agent: "Use bat to view README.md"
  │
  ▼
┌─────────────────────────────────────────┐
│ call_tool("nixpkgs_bat",               │
│          {"args": ["README.md"]})       │
└─────────────────────────────────────────┘
```

## Performance Characteristics

### Startup Performance

| Stage | Time | Memory |
|-------|------|--------|
| Load metadata (cached) | ~0.5s | ~50MB |
| Load metadata (download) | ~2-3s | ~50MB |
| Pre-register common tools | ~0.1s | +5MB |
| **Total cold start** | **~2.5s** | **~55MB** |
| **Total warm start** | **~0.6s** | **~55MB** |

### Runtime Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Search (in-memory) | ~50ms | Linear scan of 80k entries |
| Install tool | ~5ms | Add to set, generate definition |
| Execute (cold) | ~1-3s | Nix evaluation + download |
| Execute (cached) | ~100-500ms | Nix store hit |

### Optimization Opportunities

1. **Metadata Search**: Use trie or fuzzy-search library (fzf) for sub-10ms search
2. **Pre-warming**: Download common packages at startup
3. **Persistent Registry**: Save installed_tools to disk for session persistence
4. **Parallel Metadata Load**: Stream parse JSON instead of loading all at once
5. **Language**: Rewrite in Go/Rust for 10x memory reduction

## Caching Strategy

### Metadata Cache

```
~/.cache/nixpkgs-mcp/
├── nixpkgs.json          # Full package list (refreshed daily)
├── nixpkgs.json.meta     # Metadata: timestamp, hash
└── installed_tools.json  # Persisted tool registry (future)
```

**Cache Invalidation:**
- Time-based: Refresh after 24 hours
- Event-based: Clear on `nixpkgs-mcp-server --clear-cache`
- Version-based: Check nixpkgs commit hash (future)

### Tool Registry

**Current**: In-memory `set[str]` of installed tools
- Pros: Fast, simple
- Cons: Lost on restart

**Future**: JSON file persistence
```json
{
  "installed_tools": ["ripgrep", "jq", "nushell"],
  "last_updated": "2025-10-28T04:00:00Z",
  "version": "0.1.0"
}
```

## Extensibility

### Adding Custom Tool Definitions

Beyond simple `nix run`, support advanced configurations:

```python
CUSTOM_TOOLS = {
    "ripgrep": {
        "default_args": ["--json"],
        "description_override": "Fast recursive search with JSON output",
        "timeout": 60,
    },
    "nushell": {
        "entry_point": "nu",
        "supports_stdin": True,
        "script_extension": ".nu",
    }
}
```

### Tool Categories

Future: Organize tools by category for better discovery:

```
- Development (compilers, linters, formatters)
- System (monitoring, process management)
- Network (http clients, dns tools)
- Data (parsers, transformers, analyzers)
- Security (scanners, crypto tools)
```

### Integration with mcp-nixos

Combine with [mcp-nixos](https://github.com/utensils/mcp-nixos) for rich package metadata:

```
nixpkgs_search("ripgrep") →
  - Description from nixpkgs.json
  - Maintainers from mcp-nixos
  - Platforms from mcp-nixos
  - Homepage, license, etc.
```

## Security Considerations

### Sandboxing

Current: Relies on Nix's sandbox
- Packages run in isolated environment
- No network access during build
- Reproducible builds

### Input Validation

- Package names validated against metadata
- Args passed as array (no shell injection)
- Stdin limited to 1MB

### Future: Permission System

```json
{
  "permissions": {
    "network": ["curl", "wget"],
    "filesystem_write": ["git"],
    "dangerous": []
  }
}
```

## Alternative Approaches Considered

### Approach A: Static Tool Generation

**Idea**: Pre-generate all 80k tools upfront

**Pros:**
- No dynamic logic
- Simple implementation

**Cons:**
- Huge JSON (>50MB)
- Slow tool list transmission
- Overwhelming for agents

**Verdict:** ❌ Rejected

### Approach B: Search-Only Pattern

**Idea**: Single `search` and `execute` tool, no tool registration

**Pros:**
- Minimal complexity
- Always up-to-date

**Cons:**
- Two-step process for every call
- Poor UX for agents
- No tool caching

**Verdict:** ⚠️ Backup plan (Tier 1 only)

### Approach C: Lazy Loading with Notifications

**Idea**: Current approach + MCP `tools/list_changed` notifications

**Pros:**
- Best UX
- Efficient
- Scales to full nixpkgs

**Cons:**
- More complex
- Requires MCP notification support

**Verdict:** ✅ **Selected** (with notification as future enhancement)

## Future Enhancements

### Phase 1: Core Stability (Current)
- [x] Basic metadata loading
- [x] Search functionality
- [x] Execute and install tools
- [x] Pre-registered common tools
- [ ] Test suite
- [ ] Error handling improvements

### Phase 2: Performance
- [ ] Persistent tool registry
- [ ] Fuzzy search with fzf
- [ ] Parallel metadata loading
- [ ] Pre-warm common packages
- [ ] Metrics and monitoring

### Phase 3: Rich Metadata
- [ ] Integration with mcp-nixos
- [ ] Package categories
- [ ] Platform compatibility info
- [ ] Dependency visualization
- [ ] Change history tracking

### Phase 4: Advanced Features
- [ ] Tool templates (custom args, timeouts)
- [ ] Batch operations
- [ ] Package version selection
- [ ] Shell environment management
- [ ] Permission system

### Phase 5: Production
- [ ] Rewrite in Go for performance
- [ ] Comprehensive test coverage
- [ ] Documentation
- [ ] CI/CD pipeline
- [ ] Package in nixpkgs
