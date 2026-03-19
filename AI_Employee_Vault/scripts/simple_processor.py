#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Task Processor - Automatically processes action files without Qwen.

This processor:
1. Reads action files from /Needs_Action
2. Analyzes the content and type
3. Creates a simple plan in /Plans
4. Moves completed items to /Done
5. Updates Dashboard

For basic file drops and simple tasks, this runs automatically.
For complex tasks, it can optionally call Qwen Code.

Usage:
    python simple_processor.py [--vault-path PATH] [--use-qwen]

Examples:
    python simple_processor.py                      # Auto-process without Qwen
    python simple_processor.py --use-qwen           # Use Qwen for complex tasks
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


class SimpleProcessor:
    """Simple task processor that handles basic file operations."""

    def __init__(self, vault_path: str):
        """Initialize the processor."""
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.inbox = self.vault_path / 'Inbox'
        self.dashboard = self.vault_path / 'Dashboard.md'

    def read_metadata(self, filepath: Path) -> dict:
        """Read metadata from action file."""
        metadata = {}
        try:
            content = filepath.read_text(encoding='utf-8')
            in_frontmatter = False
            for line in content.split('\n'):
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                elif in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
        except Exception as e:
            print(f'Error reading metadata: {e}')
        return metadata

    def create_plan(self, action_file: Path, metadata: dict) -> Path:
        """Create a simple plan file."""
        item_type = metadata.get('type', 'unknown')
        filename = action_file.stem
        plan_file = self.plans / f'PLAN_{filename}.md'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Create simple plan based on type
        if item_type == 'file_drop':
            plan_content = f'''---
type: plan
created: {datetime.now().isoformat()}
status: in_progress
---

# Plan: Process File Drop

## Item Information
- **Original File:** {metadata.get('original_name', 'Unknown')}
- **File Type:** {metadata.get('file_type', 'unknown')}
- **Priority:** {metadata.get('priority', 'P2')}
- **Received:** {metadata.get('received', 'Unknown')}

## Actions

### 1. Review File Content
- [x] Check file type and size
- [ ] Review content (manual step)

### 2. Categorize
- [ ] Determine appropriate category
- [ ] Move to appropriate folder

### 3. Extract Action Items
- [ ] Identify any tasks from the file
- [ ] Create follow-up tasks if needed

## Processing Notes

File dropped for processing. Review the file content in Inbox folder:
- Location: `{self.inbox / metadata.get('original_name', '')}`

## Completion

- [ ] File reviewed
- [ ] Actions identified
- [ ] Move to Done

---
*Created by SimpleProcessor at {timestamp}*
'''
        else:
            plan_content = f'''---
type: plan
created: {datetime.now().isoformat()}
status: in_progress
---

# Plan: Process {item_type}

## Item Information
- **Type:** {item_type}
- **Priority:** {metadata.get('priority', 'P2')}

## Actions

- [ ] Review item content
- [ ] Identify required actions
- [ ] Execute actions
- [ ] Move to Done

---
*Created by SimpleProcessor at {timestamp}*
'''

        plan_file.write_text(plan_content, encoding='utf-8')
        return plan_file

    def move_to_done(self, action_file: Path, metadata: dict) -> Path:
        """Move action file to Done folder."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = metadata.get('original_name', action_file.stem)
        done_filename = f'COMPLETED_{original_name}_{timestamp}.md'
        done_file = self.done / done_filename

        shutil.copy2(action_file, done_file)
        action_file.unlink()  # Remove from Needs_Action

        return done_file

    def update_dashboard(self, action: str, count: int = 1):
        """Update dashboard with processing info."""
        try:
            if not self.dashboard.exists():
                return

            content = self.dashboard.read_text(encoding='utf-8')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            iso_timestamp = datetime.now().isoformat()

            # Update timestamp
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('last_updated:'):
                    lines[i] = f'last_updated: {iso_timestamp}'
                    break

            # Update pending count
            pending_count = len(list(self.needs_action.glob('*.md')))
            pending_status = '✅ Clear' if pending_count == 0 else f'⚠️ {pending_count} pending'

            content = '\n'.join(lines)
            content = content.replace(
                '| **Pending Tasks** | 0 | ✅ Clear |',
                f'| **Pending Tasks** | {pending_count} | {pending_status} |'
            )

            self.dashboard.write_text(content, encoding='utf-8')
            print('📊 Dashboard updated')

        except Exception as e:
            print(f'Warning: Could not update Dashboard: {e}')

    def process_item(self, action_file: Path) -> bool:
        """Process a single action file."""
        print(f'\n📥 Processing: {action_file.name}')
        print('-' * 50)

        try:
            # Read metadata
            metadata = self.read_metadata(action_file)
            item_type = metadata.get('type', 'unknown')

            print(f'  Type: {item_type}')
            print(f'  Priority: {metadata.get("priority", "P2")}')

            # Create plan
            print('  Creating plan...')
            plan_file = self.create_plan(action_file, metadata)
            print(f'  ✅ Plan created: {plan_file.name}')

            # Move to done
            print('  Moving to Done...')
            done_file = self.move_to_done(action_file, metadata)
            print(f'  ✅ Moved to Done: {done_file.name}')

            # Update dashboard
            self.update_dashboard('processed')

            print('✅ Processing complete')
            return True

        except Exception as e:
            print(f'❌ Processing failed: {e}')
            return False

    def process_all(self) -> dict:
        """Process all pending items."""
        stats = {'total': 0, 'processed': 0, 'failed': 0}

        items = list(self.needs_action.glob('*.md'))
        stats['total'] = len(items)

        if not items:
            print('✅ No pending items to process!')
            return stats

        print(f'📋 Found {len(items)} pending item(s)')

        for item in items:
            if self.process_item(item):
                stats['processed'] += 1
            else:
                stats['failed'] += 1

        print()
        print('=' * 50)
        print('📈 Processing Summary')
        print('-' * 30)
        print(f'  Total items: {stats["total"]}')
        print(f'  Processed: {stats["processed"]}')
        print(f'  Failed: {stats["failed"]}')

        return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Simple Task Processor - Auto-process action files'
    )
    parser.add_argument(
        '--vault-path', '-v',
        default=str(Path(__file__).parent.parent),
        help='Path to Obsidian vault (default: parent of scripts folder)'
    )
    parser.add_argument(
        '--use-qwen', '-q',
        action='store_true',
        help='Use Qwen Code for complex tasks (not implemented yet)'
    )

    args = parser.parse_args()
    vault_path = Path(args.vault_path)

    if not vault_path.exists():
        print(f'❌ Vault path does not exist: {vault_path}')
        sys.exit(1)

    print('🤖 Simple Task Processor')
    print('=' * 50)
    print(f'   Vault: {vault_path}')
    print()

    processor = SimpleProcessor(str(vault_path))
    stats = processor.process_all()

    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
