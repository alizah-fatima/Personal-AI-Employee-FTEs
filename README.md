# 🤖 AI Employee - Bronze Tier Implementation

> **Tagline:** Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

This is the **Bronze Tier** (Foundation) implementation of the Personal AI Employee FTE system. It provides the minimum viable deliverable as defined in the hackathon document.

---

## 📋 Bronze Tier Deliverables

- [x] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [x] One working Watcher script (File System monitoring)
- [x] Claude Code integration for reading/writing to the vault
- [x] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- [x] Orchestrator script to trigger Claude Code processing

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

| Component | Version | Download |
|-----------|---------|----------|
| Python | 3.13+ | [python.org](https://www.python.org/downloads/) |
| Node.js | v24+ LTS | [nodejs.org](https://nodejs.org/) |
| Claude Code | Active subscription | [claude.com](https://claude.com/product/claude-code) |
| Obsidian | v1.10.6+ (free) | [obsidian.md](https://obsidian.md/download) |

### Installation

1. **Install Python dependencies:**

```bash
cd scripts
pip install -r requirements.txt
```

2. **Verify Claude Code is installed:**

```bash
claude --version
```

3. **Open the vault in Obsidian:**

Open Obsidian and select the `AI_Employee_Vault` folder as your vault.

---

## 📁 Project Structure

```
Personal-AI-Employee-FTEs/
├── AI_Employee_Vault/          # Obsidian vault
│   ├── Dashboard.md            # Main dashboard
│   ├── Company_Handbook.md     # Rules of engagement
│   ├── Business_Goals.md       # Objectives and targets
│   ├── Inbox/                  # Raw incoming items
│   ├── Needs_Action/           # Items requiring attention
│   ├── Done/                   # Completed tasks
│   ├── Plans/                  # Active plans
│   ├── Pending_Approval/       # Awaiting approval
│   ├── Approved/               # Approved actions
│   ├── Accounting/             # Financial records
│   ├── Briefings/              # CEO briefings
│   └── Drop/                   # Drop folder for files
├── scripts/
│   ├── base_watcher.py         # Base class for watchers
│   ├── filesystem_watcher.py   # File system watcher
│   ├── orchestrator.py         # Claude Code trigger
│   └── requirements.txt        # Python dependencies
└── README.md                   # This file
```

---

## 🎯 Usage

### 1. Start the File System Watcher

The File System Watcher monitors the `Drop` folder for new files.

```bash
# From the project root
python scripts/filesystem_watcher.py

# Or with custom path
python scripts/filesystem_watcher.py --vault-path /path/to/vault
```

**What it does:**
- Monitors `AI_Employee_Vault/Drop/` for new files
- When a file is added, copies it to `Inbox/`
- Creates an action file in `Needs_Action/` with metadata
- Runs continuously until stopped (Ctrl+C)

### 2. Process Items with Claude Code

The Orchestrator triggers Claude Code to process pending items.

```bash
# Process one item (highest priority first)
python scripts/orchestrator.py

# Process all pending items
python scripts/orchestrator.py --process-all

# Check status without processing
python scripts/orchestrator.py --status

# Dry run (see what would be done)
python scripts/orchestrator.py --dry-run
```

### 3. Manual File Drop Workflow

**To process a file:**

1. Drop any file into `AI_Employee_Vault/Drop/`
2. File System Watcher detects it (if running)
3. Action file is created in `Needs_Action/`
4. Run orchestrator: `python scripts/orchestrator.py`
5. Claude Code processes the item
6. Results are logged, file moved to `Done/`

---

## 📖 Vault Folders Explained

| Folder | Purpose |
|--------|---------|
| `Inbox/` | Raw incoming items (files, emails, messages) |
| `Needs_Action/` | Items requiring attention with metadata |
| `Done/` | Completed and processed items |
| `Plans/` | Action plans created by Claude Code |
| `Pending_Approval/` | Actions awaiting human approval |
| `Approved/` | Approved actions ready for execution |
| `Accounting/` | Financial records and transactions |
| `Briefings/` | CEO briefings and reports |
| `Drop/` | Manual drop folder for files to process |

---

## 📄 Key Files

### Dashboard.md

Real-time summary of your AI Employee's status:
- Pending tasks count
- Urgent messages
- Business metrics
- System status
- Quick links

### Company_Handbook.md

Rules of engagement for your AI Employee:
- Communication standards
- Financial rules (flag payments > $500)
- Priority levels (P0-P3)
- Decision matrix
- Forbidden actions

### Business_Goals.md

Your business objectives:
- Revenue targets
- Key metrics
- Active projects
- Subscription tracking

---

## 🔧 Configuration

### Watcher Interval

By default, the File System Watcher checks every 60 seconds. To change:

```bash
python scripts/filesystem_watcher.py --interval 30
```

### Claude Code Timeout

By default, Claude Code has 300 seconds (5 minutes) per item. To change, edit `orchestrator.py`:

```python
success, output = self.run_claude(prompt, timeout=600)  # 10 minutes
```

---

## 🧪 Testing the Bronze Tier

### Test 1: File System Watcher

1. Start the watcher:
   ```bash
   python scripts/filesystem_watcher.py
   ```

2. Drop a test file:
   ```bash
   echo "Test content" > AI_Employee_Vault/Drop/test_document.txt
   ```

3. Check `Needs_Action/` for a new action file:
   ```
   FILE_<hash>_<timestamp>.md
   ```

4. Stop the watcher (Ctrl+C)

### Test 2: Claude Code Processing

1. Ensure you have a pending item in `Needs_Action/`

2. Run the orchestrator:
   ```bash
   python scripts/orchestrator.py
   ```

3. Claude Code will:
   - Read the action file
   - Read Company_Handbook.md and Business_Goals.md
   - Create a plan in `Plans/`
   - Process the item
   - Move to `Done/` when complete

### Test 3: Status Check

```bash
python scripts/orchestrator.py --status
```

Expected output:
```
📊 AI Employee Status
------------------------------
  Pending items: X
  Awaiting approval: X
  Approved & ready: X
```

---

## 🐛 Troubleshooting

### "Claude Code not found"

```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Or check if it's installed
claude --version
```

### "Module not found: watchdog"

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt
```

### Watcher not detecting files

1. Check the watcher is running:
   ```bash
   python scripts/filesystem_watcher.py
   ```

2. Verify the `Drop` folder exists:
   ```bash
   ls AI_Employee_Vault/Drop/
   ```

3. Check logs in `logs/` folder

### Claude Code processing fails

1. Check Claude Code subscription is active
2. Verify vault path is correct
3. Check `Company_Handbook.md` and `Business_Goals.md` exist
4. Review error message for details

---

## 📈 Next Steps (Silver Tier)

After mastering Bronze Tier, consider adding:

1. **Gmail Watcher** - Monitor Gmail for important emails
2. **WhatsApp Watcher** - Monitor WhatsApp for urgent messages
3. **MCP Server** - Enable external actions (send emails, etc.)
4. **Human-in-the-Loop** - Approval workflow for sensitive actions
5. **Scheduling** - Cron/Task Scheduler for automated runs

---

## 📚 Documentation

- [Personal AI Employee FTEs.md](./Personal%20AI%20Employee%20FTEs.md) - Full hackathon document
- [Dashboard.md](./AI_Employee_Vault/Dashboard.md) - Main dashboard
- [Company_Handbook.md](./AI_Employee_Vault/Company_Handbook.md) - Rules of engagement
- [Business_Goals.md](./AI_Employee_Vault/Business_Goals.md) - Objectives

---

## 🤝 Contributing

This is a hackathon project. Feel free to:
- Add new watcher scripts
- Improve Claude Code prompts
- Enhance the Dashboard
- Add MCP server integrations

---

## 📄 License

This project is part of the Personal AI Employee Hackathon 2026.

---

**Built with ❤️ using Claude Code and Obsidian**

*Version: Bronze Tier v1.0 | Date: 2026-03-17*
