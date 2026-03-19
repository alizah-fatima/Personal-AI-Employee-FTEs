#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Watcher - Abstract base class for all AI Employee watchers.

This module provides the foundation for all watcher scripts that monitor
various inputs (Gmail, WhatsApp, filesystem, etc.) and create actionable
files for Claude Code to process.

Usage:
    Extend this class to create specific watchers:
    
    class GmailWatcher(BaseWatcher):
        def check_for_updates(self) -> list:
            # Implement Gmail checking logic
            pass
        
        def create_action_file(self, item) -> Path:
            # Implement action file creation
            pass
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher scripts.
    
    All watchers follow this pattern:
    1. Run continuously in background
    2. Periodically check for new items
    3. Create .md files in /Needs_Action folder for new items
    4. Track processed items to avoid duplicates
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        self.check_interval = check_interval
        self.processed_ids: set = set()
        self.running = False
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Create logs directory (inside vault)
        log_dir = self.vault_path / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for this watcher
        log_file = log_dir / f'{self.__class__.__name__.lower()}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Ensure directories exist
        self._ensure_directories()
        
        self.logger.info(f'Initialized {self.__class__.__name__}')
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.vault_path,
            self.needs_action,
            self.inbox,
            self.vault_path / 'Done',
            self.vault_path / 'Plans',
            self.vault_path / 'Pending_Approval',
            self.vault_path / 'Approved',
            self.vault_path / 'Accounting',
            self.vault_path / 'Briefings',
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items to process.
        
        Returns:
            list: List of new items (each item should be a dict with relevant data)
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: dict) -> Path:
        """
        Create a .md action file in /Needs_Action folder.
        
        Args:
            item: The item to process
            
        Returns:
            Path: Path to the created action file
        """
        pass
    
    def _generate_filename(self, prefix: str, unique_id: str) -> str:
        """
        Generate a standardized filename.
        
        Args:
            prefix: File prefix (e.g., 'EMAIL', 'WHATSAPP', 'FILE')
            unique_id: Unique identifier for the item
            
        Returns:
            str: Filename in format PREFIX_ID_TIMESTAMP.md
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f'{prefix}_{unique_id}_{timestamp}.md'
    
    def _get_priority(self, content: str) -> str:
        """
        Determine priority based on content keywords.
        
        Args:
            content: Text content to analyze
            
        Returns:
            str: Priority level ('P0', 'P1', 'P2', 'P3')
        """
        content_lower = content.lower()
        
        # P0 - Critical
        p0_keywords = ['emergency', 'urgent', 'asap', 'critical', 'immediately']
        if any(keyword in content_lower for keyword in p0_keywords):
            return 'P0'
        
        # P1 - High
        p1_keywords = ['important', 'deadline', 'today', 'as soon as possible']
        if any(keyword in content_lower for keyword in p1_keywords):
            return 'P1'
        
        # P2 - Normal (default)
        return 'P2'
    
    def run(self):
        """
        Main run loop for the watcher.
        
        Continuously checks for updates and creates action files.
        """
        self.running = True
        self.logger.info(f'Starting {self.__class__.__name__} (interval: {self.check_interval}s)')
        
        try:
            while self.running:
                try:
                    items = self.check_for_updates()
                    self.logger.debug(f'Found {len(items)} new items')
                    
                    for item in items:
                        try:
                            filepath = self.create_action_file(item)
                            self.logger.info(f'Created action file: {filepath.name}')
                        except Exception as e:
                            self.logger.error(f'Error creating action file: {e}')
                    
                except Exception as e:
                    self.logger.error(f'Error in check loop: {e}')
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info('Watcher stopped by user')
        finally:
            self.running = False
    
    def stop(self):
        """Stop the watcher."""
        self.running = False
        self.logger.info('Stopping watcher...')


def main():
    """
    Main entry point for running the watcher directly.
    
    This should be overridden by subclasses.
    """
    print("BaseWatcher is an abstract class. Use a specific watcher implementation.")
    print("Example: python filesystem_watcher.py")


if __name__ == "__main__":
    main()
