#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Main script to trigger Qwen Code for task processing.

This script:
1. Checks /Needs_Action folder for pending items
2. Triggers Qwen Code to process them
3. Updates Dashboard.md with results
4. Manages the overall AI Employee workflow

Usage:
    python orchestrator.py [--vault-path PATH] [--process-all] [--dry-run]

Examples:
    python orchestrator.py                          # Process one item
    python orchestrator.py --process-all            # Process all pending items
    python orchestrator.py --vault-path /path/to/vault
    python orchestrator.py --dry-run                # Show what would be done
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


class Orchestrator:
    """
    Main orchestrator for the AI Employee.
    
    Coordinates between watchers, Claude Code, and the vault.
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize the orchestrator.
        
        Args:
            vault_path: Path to the Obsidian vault root
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        # Ensure directories exist
        for directory in [self.needs_action, self.done, self.plans, 
                          self.pending_approval, self.approved]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_pending_items(self) -> List[Path]:
        """
        Get list of pending items in /Needs_Action.
        
        Returns:
            List[Path]: List of pending .md files, sorted by priority
        """
        if not self.needs_action.exists():
            return []
        
        items = list(self.needs_action.glob('*.md'))
        
        # Sort by priority (P0 first, then P1, P2, P3)
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        
        def get_priority(filepath: Path) -> int:
            try:
                content = filepath.read_text(encoding='utf-8')
                for line in content.split('\n'):
                    if line.startswith('priority:'):
                        priority = line.split(':')[1].strip()
                        return priority_order.get(priority, 2)
            except Exception:
                pass
            return 2  # Default P2
        
        return sorted(items, key=get_priority)
    
    def get_approval_items(self) -> List[Path]:
        """
        Get list of items pending approval.
        
        Returns:
            List[Path]: List of approval request files
        """
        if not self.pending_approval.exists():
            return []
        
        return list(self.pending_approval.glob('*.md'))
    
    def get_approved_items(self) -> List[Path]:
        """
        Get list of approved items ready for execution.
        
        Returns:
            List[Path]: List of approved files
        """
        if not self.approved.exists():
            return []
        
        return list(self.approved.glob('*.md'))
    
    def read_item_metadata(self, filepath: Path) -> dict:
        """
        Read metadata from an action file.
        
        Args:
            filepath: Path to the .md file
            
        Returns:
            dict: Metadata dictionary
        """
        metadata = {}
        try:
            content = filepath.read_text(encoding='utf-8')
            
            # Parse frontmatter
            in_frontmatter = False
            for line in content.split('\n'):
                if line.strip() == '---':
                    if not in_frontmatter:
                        in_frontmatter = True
                    else:
                        break
                elif in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
                    
        except Exception as e:
            print(f'Error reading metadata from {filepath}: {e}')
        
        return metadata
    
    def create_claude_prompt(self, item: Path) -> str:
        """
        Create a prompt for Claude Code to process an item.
        
        Args:
            item: Path to the action file
            
        Returns:
            str: Prompt for Claude Code
        """
        metadata = self.read_item_metadata(item)
        item_type = metadata.get('type', 'unknown')
        priority = metadata.get('priority', 'P2')
        
        prompt = f'''Process this {item_type} item from the AI Employee vault.

**Item:** {item.name}
**Priority:** {priority}
**Location:** {item}

**Your Tasks:**

1. **Read and Analyze:**
   - Read the action file content
   - Read the Company_Handbook.md for rules of engagement
   - Read the Business_Goals.md for context

2. **Create Action Plan:**
   - Create a Plan.md file in /Plans folder with:
     - Summary of the item
     - Step-by-step actions needed
     - Checkboxes for each action

3. **Execute Actions:**
   - For routine actions: Execute directly using file system tools
   - For sensitive actions: Create approval request in /Pending_Approval
   - Update the action file with processing notes

4. **Complete Processing:**
   - Move processed item to /Done with timestamp
   - Update Dashboard.md with summary
   - Log all actions taken

**Rules to Follow:**
- Always be polite and professional
- Flag payments over $500 for approval
- Never send messages without approval
- Log all actions for audit purposes
- Follow the priority levels in Company_Handbook.md

**Output Format:**
After processing, provide a summary:
- What was processed
- Actions taken
- Any approvals needed
- Next steps

Begin processing now.'''
        
        return prompt
    
    def run_qwen(self, prompt: str, timeout: int = 300) -> Tuple[bool, str]:
        """
        Run Qwen Code with the given prompt.

        Args:
            prompt: The prompt to send to Qwen
            timeout: Maximum execution time in seconds

        Returns:
            Tuple[bool, str]: (success, output)
        """
        try:
            # Check if qwen command is available (use cmd to find it)
            result = subprocess.run(
                ['cmd', '/c', 'qwen', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return False, 'Qwen Code not found. Please install Qwen Code first.'

            # Run Qwen with the prompt (use cmd /c to properly invoke npm command)
            print('🤖 Running Qwen Code...')
            print('-' * 50)

            qwen_process = subprocess.Popen(
                ['cmd', '/c', 'qwen', '--prompt', prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.vault_path)
            )

            try:
                stdout, stderr = qwen_process.communicate(timeout=timeout)

                if qwen_process.returncode == 0:
                    return True, stdout
                else:
                    return False, f'Qwen exited with code {qwen_process.returncode}\n\n{stderr}'

            except subprocess.TimeoutExpired:
                qwen_process.kill()
                return False, f'Qwen timed out after {timeout} seconds'

        except FileNotFoundError:
            return False, 'Qwen Code command not found. Please install it first.'
        except Exception as e:
            return False, f'Error running Qwen: {e}'
    
    def update_dashboard(self, summary: str, action: str = "processed"):
        """
        Update the Dashboard.md with processing summary.

        Args:
            summary: Summary of actions taken
            action: Type of action (processed, created, completed, etc.)
        """
        try:
            if not self.dashboard.exists():
                print('Dashboard.md not found, skipping update')
                return

            content = self.dashboard.read_text(encoding='utf-8')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            iso_timestamp = datetime.now().isoformat()

            # 1. Update last_updated timestamp in frontmatter
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('last_updated:'):
                    lines[i] = f'last_updated: {iso_timestamp}'
                    break

            # 2. Update Recent Activity section
            activity_entry = f'| {timestamp} | {action} | ✅ Complete |'
            
            # Find the Recent Activity section and add entry
            in_activity_section = False
            new_lines = []
            header_found = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                
                # Find the Recent Activity header
                if '## 📝 Recent Activity' in line:
                    header_found = True
                    continue
                
                # Find the table header line
                if header_found and '| Timestamp | Action | Status |' in line:
                    in_activity_section = True
                    continue
                
                # Skip the separator line
                if in_activity_section and line.strip().startswith('|---'):
                    continue
                
                # Add our entry after the table header
                if in_activity_section and line.strip().startswith('| Timestamp'):
                    new_lines.append(activity_entry)
                    in_activity_section = False
                    # Skip the placeholder line
                    if i + 1 < len(lines) and '- | - | -' in lines[i + 1]:
                        lines[i + 1] = ''  # Remove placeholder
            
            content = '\n'.join(new_lines)

            # 3. Update Pending Tasks count in Quick Status
            pending_count = len(self.get_pending_items())
            pending_status = '✅ Clear' if pending_count == 0 else f'⚠️ {pending_count} pending'
            
            content = content.replace(
                '| **Pending Tasks** | 0 | ✅ Clear |',
                f'| **Pending Tasks** | {pending_count} | {pending_status} |'
            )

            # Write updated content
            self.dashboard.write_text(content, encoding='utf-8')
            print('📊 Dashboard updated')

        except Exception as e:
            print(f'Warning: Could not update Dashboard: {e}')
    
    def process_item(self, item: Path, dry_run: bool = False) -> bool:
        """
        Process a single item with Qwen Code.

        Args:
            item: Path to the action file
            dry_run: If True, only show what would be done

        Returns:
            bool: True if processing succeeded
        """
        print(f'\n📥 Processing: {item.name}')
        print('-' * 50)

        if dry_run:
            print('[DRY RUN] Would process this item with Qwen Code')
            metadata = self.read_item_metadata(item)
            print(f'  Type: {metadata.get("type", "unknown")}')
            print(f'  Priority: {metadata.get("priority", "P2")}')
            return True

        # Create prompt
        prompt = self.create_claude_prompt(item)

        # Run Qwen
        success, output = self.run_qwen(prompt)

        if success:
            print('✅ Processing complete')
            # Update dashboard with item name and type
            metadata = self.read_item_metadata(item)
            item_type = metadata.get('type', 'item')
            self.update_dashboard(f'Processed {item_type}: {item.name}', 'processed')
            return True
        else:
            print(f'❌ Processing failed: {output}')
            return False
    
    def process_all(self, dry_run: bool = False) -> dict:
        """
        Process all pending items.
        
        Args:
            dry_run: If True, only show what would be done
            
        Returns:
            dict: Processing statistics
        """
        stats = {
            'total': 0,
            'processed': 0,
            'failed': 0,
            'approvals_pending': 0,
        }
        
        # Get pending items
        items = self.get_pending_items()
        stats['total'] = len(items)
        
        if not items:
            print('✅ No pending items to process!')
            return stats
        
        print(f'📋 Found {len(items)} pending item(s)')
        
        # Process each item
        for item in items:
            if self.process_item(item, dry_run):
                stats['processed'] += 1
            else:
                stats['failed'] += 1
        
        # Check for approvals
        approvals = self.get_approval_items()
        stats['approvals_pending'] = len(approvals)

        if approvals:
            print(f'\n⏳ {len(approvals)} item(s) awaiting your approval')

        # Update dashboard with final status
        if not dry_run:
            action = f'Processed {stats["processed"]} item(s)' if stats['processed'] > 0 else 'Checked pending items'
            self.update_dashboard(action, 'batch_processed')

        return stats
    
    def status(self) -> dict:
        """
        Get current status of the vault.
        
        Returns:
            dict: Status information
        """
        return {
            'pending': len(self.get_pending_items()),
            'approvals_pending': len(self.get_approval_items()),
            'approved_ready': len(self.get_approved_items()),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Employee Orchestrator - Process tasks with Claude Code'
    )
    parser.add_argument(
        '--vault-path', '-v',
        default=str(Path(__file__).parent.parent),
        help='Path to Obsidian vault (default: parent of scripts folder)'
    )
    parser.add_argument(
        '--process-all', '-a',
        action='store_true',
        help='Process all pending items (default: process one)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without actually processing'
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show current status and exit'
    )
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    
    if not vault_path.exists():
        print(f'❌ Vault path does not exist: {vault_path}')
        print('Please create the vault directory first.')
        sys.exit(1)
    
    orchestrator = Orchestrator(str(vault_path))
    
    # Show status if requested
    if args.status:
        status = orchestrator.status()
        print('📊 AI Employee Status')
        print('-' * 30)
        print(f'  Pending items: {status["pending"]}')
        print(f'  Awaiting approval: {status["approvals_pending"]}')
        print(f'  Approved & ready: {status["approved_ready"]}')
        sys.exit(0)
    
    # Print header
    print('🤖 AI Employee Orchestrator')
    print('=' * 50)
    print(f'   Vault: {vault_path}')
    print(f'   Mode: {"Dry Run" if args.dry_run else "Live"}')
    print()
    
    # Process items
    if args.process_all:
        stats = orchestrator.process_all(dry_run=args.dry_run)
    else:
        # Process just the highest priority item
        items = orchestrator.get_pending_items()
        if items:
            stats = orchestrator.process_item(items[0], dry_run=args.dry_run)
            stats = {'total': 1, 'processed': 1 if stats else 0, 'failed': 0 if stats else 1}
        else:
            print('✅ No pending items to process!')
            stats = {'total': 0, 'processed': 0, 'failed': 0}
    
    # Print summary
    print()
    print('=' * 50)
    print('📈 Processing Summary')
    print('-' * 30)
    print(f'  Total items: {stats.get("total", 0)}')
    print(f'  Processed: {stats.get("processed", 0)}')
    print(f'  Failed: {stats.get("failed", 0)}')
    if 'approvals_pending' in stats:
        print(f'  Awaiting approval: {stats["approvals_pending"]}')
    
    print()
    if stats.get('failed', 0) > 0:
        print('⚠️  Some items failed to process. Check logs for details.')
        sys.exit(1)
    else:
        print('✅ All done!')
        sys.exit(0)


if __name__ == "__main__":
    main()
