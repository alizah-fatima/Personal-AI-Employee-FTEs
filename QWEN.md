# Personal AI Employee FTEs - Project Context

## Project Overview

This repository contains a comprehensive architectural blueprint and hackathon guide for building a **"Digital FTE" (Full-Time Equivalent)** — an autonomous AI agent that proactively manages personal and business affairs 24/7. The project uses **Claude Code** as the reasoning engine and **Obsidian** (local Markdown) as the dashboard/memory system.

### Core Architecture

The system follows a **Perception → Reasoning → Action** pattern:

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Perception** | Python "Watcher" scripts | Monitor Gmail, WhatsApp, filesystems for triggers |
| **Reasoning** | Claude Code | Analyzes tasks, creates plans, makes decisions |
| **Action** | MCP Servers | Execute actions (send emails, click buttons, etc.) |
| **Memory/GUI** | Obsidian Vault | Dashboard, task tracking, knowledge base |

### Key Concepts

- **Watchers**: Lightweight Python scripts that run continuously, monitoring inputs and creating `.md` files in `/Needs_Action` folder
- **Ralph Wiggum Loop**: A Stop hook pattern that keeps Claude iterating until multi-step tasks are complete
- **Human-in-the-Loop (HITL)**: Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
- **MCP (Model Context Protocol)**: Standardized interface for Claude to interact with external systems

## Directory Structure

```
Personal-AI-Employee-FTEs/
├── Personal AI Employee FTEs.md    # Main documentation (1200+ lines)
├── skills-lock.json                # Skill version tracking
├── QWEN.md                         # This file
├── .qwen/
│   └── skills/
│       └── browsing-with-playwright/   # Browser automation skill
│           ├── SKILL.md                # Skill documentation
│           ├── scripts/
│           │   ├── mcp-client.py       # Universal MCP client (HTTP/stdio)
│           │   ├── start-server.sh     # Start Playwright MCP server
│           │   ├── stop-server.sh      # Stop Playwright MCP server
│           │   └── verify.py           # Server health check
│           └── references/
│               └── playwright-tools.md # 22 browser automation tools
└── .git/
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers & automation |

### Playwright MCP Server (Browser Automation)

The project includes a browser automation skill using Playwright MCP:

```bash
# Start the server (port 8808)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Verify server is running
python .qwen/skills/browsing-with-playwright/scripts/verify.py

# Stop the server
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh
```

### Using the MCP Client

The `mcp-client.py` is a universal MCP client supporting both HTTP and stdio transports:

```bash
# List available tools
python mcp-client.py list --url http://localhost:8808

# Call a tool
python mcp-client.py call -u http://localhost:8808 -t browser_navigate \
  -p '{"url": "https://example.com"}'

# Take a screenshot
python mcp-client.py call -u http://localhost:8808 -t browser_take_screenshot \
  -p '{"type": "png", "fullPage": true}'

# Get page snapshot (for element interaction)
python mcp-client.py call -u http://localhost:8808 -t browser_snapshot -p '{}'
```

### Key MCP Tools Available

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to URL |
| `browser_snapshot` | Get accessibility snapshot (element refs) |
| `browser_click` | Click element (requires `ref` from snapshot) |
| `browser_type` | Type text into input |
| `browser_fill_form` | Fill multiple form fields |
| `browser_take_screenshot` | Capture screenshot |
| `browser_evaluate` | Execute JavaScript |
| `browser_run_code` | Run Playwright code snippet |

See `.qwen/skills/browsing-with-playwright/references/playwright-tools.md` for all 22 tools.

## Development Conventions

### Skill Structure

Each skill follows this pattern:
1. **SKILL.md**: Main documentation with usage examples
2. **scripts/**: Executable scripts for server lifecycle and utilities
3. **references/**: Generated tool documentation (from `mcp-client.py emit`)

### MCP Client Usage

The `mcp-client.py` is bundled with skills and supports:
- **HTTP transport**: For remote/local MCP servers (`--url`)
- **Stdio transport**: For spawning local MCP servers (`--stdio`)
- **Tool listing**: `list` command
- **Tool calling**: `call` command with JSON params
- **Schema emission**: `emit --format markdown|json`

### File-Based Communication

Agents communicate via the Obsidian vault using file movements:
- `/Inbox` → New items to process
- `/Needs_Action` → Items requiring attention
- `/In_Progress/<agent>/` → Claimed items (prevents double-work)
- `/Pending_Approval/` → Actions awaiting human approval
- `/Approved/` → Approved actions (triggers execution)
- `/Done/` → Completed tasks

## Hackathon Tiers

The project defines achievement tiers for building your AI Employee:

| Tier | Time | Deliverables |
|------|------|--------------|
| **Bronze** | 8-12 hrs | Obsidian dashboard, 1 watcher, basic Claude integration |
| **Silver** | 20-30 hrs | 2+ watchers, MCP server, HITL workflow, scheduling |
| **Gold** | 40+ hrs | Full integration, Odoo accounting, Ralph Wiggum loop |
| **Platinum** | 60+ hrs | Cloud deployment, work-zone specialization, A2A upgrade |

## Key Files

| File | Description |
|------|-------------|
| `Personal AI Employee FTEs.md` | Complete architectural blueprint (1201 lines) |
| `skills-lock.json` | Tracks installed skill versions and hashes |
| `.qwen/skills/browsing-with-playwright/SKILL.md` | Browser automation skill guide |
| `.qwen/skills/browsing-with-playwright/scripts/mcp-client.py` | Universal MCP client (350+ lines) |

## Usage Notes

### Important Flags

- `--shared-browser-context`: Required for Playwright MCP to maintain browser state across calls
- Without it, each call gets a fresh browser context (cookies/session lost)

### Security Rules

- Vault sync includes only markdown/state files
- Secrets **never** sync (`.env`, tokens, WhatsApp sessions, banking credentials)
- Cloud agents work in "draft-only" mode; Local executes sensitive actions

### Common Workflows

**Form Submission:**
1. Navigate to page
2. Get snapshot to find element refs
3. Fill form fields using refs
4. Click submit
5. Wait for confirmation
6. Screenshot result

**Data Extraction:**
1. Navigate to page
2. Get snapshot (contains text content)
3. Use `browser_evaluate` for complex extraction
4. Process results

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not responding | Run `bash scripts/stop-server.sh && bash scripts/start-server.sh` |
| Element not found | Run `browser_snapshot` first to get current refs |
| Click fails | Try `browser_hover` first, then click |
| Form not submitting | Use `"submit": true` with `browser_type` |

## External Resources

- [Claude Code Documentation](https://claude.com/product/claude-code)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [MCP Server Documentation](https://github.com/AlanOgic/mcp-odoo-adv)
- [Ralph Wiggum Pattern](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
