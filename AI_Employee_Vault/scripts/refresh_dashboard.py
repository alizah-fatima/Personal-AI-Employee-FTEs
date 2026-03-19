#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Refresh - Update Dashboard with current vault status.

This script updates the Dashboard.md with real-time counts from all folders.
Run this periodically to keep your Dashboard fresh.

Usage:
    python refresh_dashboard.py [--vault-path PATH]

Examples:
    python refresh_dashboard.py
    python refresh_dashboard.py --vault-path /path/to/vault
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime


def count_md_files(folder: Path) -> int:
    """Count .md files in a folder."""
    if not folder.exists():
        return 0
    return len(list(folder.glob('*.md')))


def refresh_dashboard(vault_path: Path):
    """Refresh the Dashboard with current status."""
    dashboard = vault_path / 'Dashboard.md'
    
    if not dashboard.exists():
        print('❌ Dashboard.md not found!')
        return False
    
    # Count items in each folder
    needs_action = vault_path / 'Needs_Action'
    pending_approval = vault_path / 'Pending_Approval'
    approved = vault_path / 'Approved'
    done = vault_path / 'Done'
    plans = vault_path / 'Plans'
    inbox = vault_path / 'Inbox'
    
    pending_count = count_md_files(needs_action)
    approval_count = count_md_files(pending_approval)
    approved_count = count_md_files(approved)
    done_count = count_md_files(done)
    plan_count = count_md_files(plans)
    inbox_count = count_md_files(inbox)
    
    # Determine status
    pending_status = '✅ Clear' if pending_count == 0 else f'⚠️ {pending_count} pending'
    approval_status = '✅ Clear' if approval_count == 0 else f'⏳ {approval_count} awaiting'
    inbox_status = '✅ Clear' if inbox_count == 0 else f'📬 {inbox_count} new'
    plan_status = f'📋 {plan_count} active' if plan_count > 0 else '📝 Not set up'
    
    # Read dashboard
    content = dashboard.read_text(encoding='utf-8')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    iso_timestamp = datetime.now().isoformat()
    
    # Update last_updated
    content = re.sub(
        r'^last_updated:.*$',
        f'last_updated: {iso_timestamp}',
        content,
        flags=re.MULTILINE
    )
    
    # Update Quick Status table using regex
    content = re.sub(
        r'\| \*\*Pending Tasks\*\* \| .+ \|',
        f'| **Pending Tasks** | {pending_count} | {pending_status} |',
        content
    )
    content = re.sub(
        r'\| \*\*Urgent Messages\*\* \| .+ \|',
        f'| **Urgent Messages** | {inbox_count} | {inbox_status} |',
        content
    )
    content = re.sub(
        r'\| \*\*Pending Approvals\*\* \| .+ \|',
        f'| **Pending Approvals** | {approval_count} | {approval_status} |',
        content
    )
    content = re.sub(
        r'\| \*\*Active Projects\*\* \| .+ \|',
        f'| **Active Projects** | {plan_count} | {plan_status} |',
        content
    )
    
    # Write updated dashboard
    dashboard.write_text(content, encoding='utf-8')
    
    print('📊 Dashboard Refreshed!')
    print('-' * 40)
    print(f'  Pending Items:     {pending_count}')
    print(f'  Plans:             {plan_count}')
    print(f'  Approvals:         {approval_count}')
    print(f'  Completed:         {done_count}')
    print(f'  Last Updated:      {timestamp}')
    print('-' * 40)
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Refresh Dashboard with current vault status'
    )
    parser.add_argument(
        '--vault-path', '-v',
        default=str(Path(__file__).parent.parent),
        help='Path to Obsidian vault (default: parent of scripts folder)'
    )
    
    args = parser.parse_args()
    vault_path = Path(args.vault_path)
    
    if not vault_path.exists():
        print(f'❌ Vault path does not exist: {vault_path}')
        sys.exit(1)
    
    success = refresh_dashboard(vault_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
