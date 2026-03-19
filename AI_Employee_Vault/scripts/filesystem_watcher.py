#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Watcher - Monitors a drop folder for new files.

This watcher monitors the /Drop folder for any new files. When a file is added,
it creates a corresponding action file in /Needs_Action with metadata, allowing
Claude Code to process the file.

Usage:
    python filesystem_watcher.py [--vault-path PATH] [--interval SECONDS]

Examples:
    python filesystem_watcher.py
    python filesystem_watcher.py --vault-path /path/to/vault --interval 30
"""

import sys
import shutil
import time
import hashlib
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    """
    Event handler for the drop folder.
    
    Watches for new files and triggers action file creation.
    """
    
    def __init__(self, watcher: 'FileSystemWatcher'):
        """
        Initialize the handler.
        
        Args:
            watcher: The parent FileSystemWatcher instance
        """
        super().__init__()
        self.watcher = watcher
    
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event: The file system event
        """
        if event.is_directory:
            return
        
        source_path = Path(event.src_path)
        
        # Skip hidden files and temporary files
        if source_path.name.startswith('.') or source_path.suffix in ['.tmp', '.swp']:
            return
        
        self.watcher.logger.info(f'New file detected: {source_path.name}')
        self.watcher.process_file(source_path)


class FileSystemWatcher(BaseWatcher):
    """
    Watcher that monitors a drop folder for new files.
    
    When files are added to /Drop folder, this watcher:
    1. Copies the file to /Inbox
    2. Creates a metadata .md file in /Needs_Action
    3. Logs the action for audit purposes
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the File System Watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (not used with watchdog)
        """
        super().__init__(vault_path, check_interval)
        
        self.drop_folder = self.vault_path / 'Drop'
        self.inbox = self.vault_path / 'Inbox'
        self.processed_files: set = set()
        
        # Ensure drop folder exists
        self.drop_folder.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f'Monitoring drop folder: {self.drop_folder}')
    
    def _get_file_hash(self, filepath: Path) -> str:
        """
        Calculate MD5 hash of a file for unique identification.
        
        Args:
            filepath: Path to the file
            
        Returns:
            str: MD5 hash of the file
        """
        hash_md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()[:12]  # Use first 12 chars for brevity
    
    def process_file(self, source_path: Path):
        """
        Process a newly detected file.
        
        Args:
            source_path: Path to the new file
        """
        try:
            # Generate unique ID
            file_hash = self._get_file_hash(source_path)
            
            # Check if already processed
            if file_hash in self.processed_files:
                self.logger.debug(f'File already processed: {source_path.name}')
                return
            
            # Copy file to Inbox
            dest_path = self.inbox / source_path.name
            shutil.copy2(source_path, dest_path)
            self.logger.info(f'Copied file to Inbox: {dest_path.name}')
            
            # Get file metadata
            file_stat = source_path.stat()
            file_size = file_stat.st_size
            file_type = source_path.suffix.lower()
            
            # Create action file in Needs_Action
            action_file = self.create_action_file({
                'original_name': source_path.name,
                'file_hash': file_hash,
                'file_size': file_size,
                'file_type': file_type,
                'source_path': str(source_path),
                'inbox_path': str(dest_path),
            })
            
            self.processed_files.add(file_hash)
            self.logger.info(f'Processed file: {source_path.name} -> {action_file.name}')
            
        except Exception as e:
            self.logger.error(f'Error processing file {source_path}: {e}')
            raise
    
    def check_for_updates(self) -> list:
        """
        Check for new files in the drop folder.
        
        This method is called periodically but the actual watching
        is done by the watchdog Observer. This is a fallback check.
        
        Returns:
            list: List of new files to process
        """
        new_files = []
        
        try:
            for file_path in self.drop_folder.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    file_hash = self._get_file_hash(file_path)
                    if file_hash not in self.processed_files:
                        new_files.append(file_path)
        except Exception as e:
            self.logger.error(f'Error checking drop folder: {e}')
        
        return new_files
    
    def create_action_file(self, item: dict) -> Path:
        """
        Create a .md action file in /Needs_Action folder.
        
        Args:
            item: Dictionary containing file metadata
            
        Returns:
            Path: Path to the created action file
        """
        # Generate filename
        filename = self._generate_filename('FILE', item['file_hash'])
        filepath = self.needs_action / filename
        
        # Determine priority based on file type
        priority = 'P2'  # Default
        if item['file_type'] in ['.pdf', '.doc', '.docx']:
            priority = 'P1'  # Documents are usually important
        
        # Create content
        content = f'''---
type: file_drop
original_name: {item['original_name']}
file_hash: {item['file_hash']}
file_size: {item['file_size']} bytes
file_type: {item['file_type']}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
inbox_path: {item['inbox_path']}
---

# File Drop for Processing

## File Information

- **Original Name:** {item['original_name']}
- **File Type:** {item['file_type'].upper()}
- **File Size:** {self._format_size(item['file_size'])}
- **Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Location:** `{item['inbox_path']}`

## Content Summary

<!-- AI Employee: Analyze the file content and summarize here -->

## Suggested Actions

- [ ] Review file content
- [ ] Categorize and file appropriately
- [ ] Extract any action items
- [ ] Move original to appropriate folder
- [ ] Archive after processing

## Processing Notes

<!-- AI Employee: Add notes during processing -->

---
*Created by FileSystemWatcher*
'''
        
        # Write file
        filepath.write_text(content, encoding='utf-8')
        return filepath
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f'{size_bytes:.2f} {unit}'
            size_bytes /= 1024.0
        return f'{size_bytes:.2f} TB'
    
    def run(self):
        """
        Main run loop for the File System Watcher.
        
        Uses watchdog Observer for real-time file monitoring.
        """
        self.running = True
        
        # Setup watchdog observer
        event_handler = DropFolderHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.drop_folder), recursive=False)
        observer.start()
        
        self.logger.info(f'FileSystemWatcher started - monitoring {self.drop_folder}')
        
        try:
            while self.running:
                time.sleep(1)  # Keep alive, watchdog handles events
                
        except KeyboardInterrupt:
            self.logger.info('Watcher stopped by user')
        finally:
            observer.stop()
            observer.join()
            self.running = False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='File System Watcher - Monitor drop folder for new files'
    )
    parser.add_argument(
        '--vault-path', '-v',
        default=str(Path(__file__).parent.parent),
        help='Path to Obsidian vault (default: parent of scripts folder)'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    
    if not vault_path.exists():
        print(f'Error: Vault path does not exist: {vault_path}')
        print('Please create the vault directory first.')
        sys.exit(1)
    
    print(f'🔍 File System Watcher')
    print(f'   Vault: {vault_path}')
    print(f'   Drop Folder: {vault_path / "Drop"}')
    print(f'   Interval: {args.interval}s')
    print()
    print('📥 Drop files into the "Drop" folder to trigger processing.')
    print('   Press Ctrl+C to stop.')
    print()
    
    watcher = FileSystemWatcher(str(vault_path), args.interval)
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        print('\n👋 Watcher stopped.')


if __name__ == "__main__":
    main()
