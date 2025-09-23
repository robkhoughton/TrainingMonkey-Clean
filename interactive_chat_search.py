#!/usr/bin/env python3
"""
Interactive Cursor Chat History Search Tool
Provides a user-friendly interface to search through Cursor chat history
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional

class CursorChatSearcher:
    def __init__(self):
        self.history_path = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Cursor" / "User" / "History"
        self.results = []
        
    def get_history_path(self) -> Path:
        """Get the Cursor history path"""
        return self.history_path
    
    def validate_path(self) -> bool:
        """Check if the history path exists"""
        if not self.history_path.exists():
            print(f"❌ Cursor history path not found: {self.history_path}")
            print("Make sure Cursor is installed and you have chat history.")
            return False
        return True
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats"""
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y", 
            "%m-%d-%Y",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %H:%M"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    def get_date_range(self) -> tuple[datetime, datetime]:
        """Get date range from user input"""
        print("\n📅 Date Range Selection:")
        print("1. Last N days")
        print("2. Specific date range")
        print("3. All time")
        
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == "1":
            try:
                days = int(input("Enter number of days (default 7): ") or "7")
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                return start_date, end_date
            except ValueError:
                print("Invalid number, using default 7 days")
                return datetime.now() - timedelta(days=7), datetime.now()
        
        elif choice == "2":
            while True:
                start_str = input("Start date (YYYY-MM-DD or MM/DD/YYYY): ").strip()
                start_date = self.parse_date(start_str)
                if start_date:
                    break
                print("Invalid date format. Try YYYY-MM-DD or MM/DD/YYYY")
            
            while True:
                end_str = input("End date (YYYY-MM-DD or MM/DD/YYYY, or press Enter for today): ").strip()
                if not end_str:
                    end_date = datetime.now()
                    break
                end_date = self.parse_date(end_str)
                if end_date:
                    break
                print("Invalid date format. Try YYYY-MM-DD or MM/DD/YYYY")
            
            return start_date, end_date
        
        else:  # All time
            return datetime(2020, 1, 1), datetime.now()
    
    def get_search_options(self) -> Dict[str, Any]:
        """Get search options from user"""
        print("\n🔍 Search Options:")
        
        keyword = input("Enter keyword to search for (or press Enter for all): ").strip()
        
        print("\nFile types to search:")
        print("1. All files")
        print("2. Markdown files only (.md)")
        print("3. Code files (.py, .js, .tsx, etc.)")
        print("4. Custom file extensions")
        
        file_choice = input("Choose file type (1-4, default 1): ").strip() or "1"
        
        file_extensions = []
        if file_choice == "2":
            file_extensions = [".md"]
        elif file_choice == "3":
            file_extensions = [".py", ".js", ".tsx", ".ts", ".html", ".css", ".sql", ".json"]
        elif file_choice == "4":
            extensions = input("Enter file extensions separated by commas (e.g., .md,.py): ").strip()
            file_extensions = [ext.strip() for ext in extensions.split(",") if ext.strip()]
        
        show_content = input("Show content preview? (y/N): ").strip().lower() == 'y'
        case_sensitive = input("Case sensitive search? (y/N): ").strip().lower() == 'y'
        
        return {
            'keyword': keyword,
            'file_extensions': file_extensions,
            'show_content': show_content,
            'case_sensitive': case_sensitive
        }
    
    def search_conversations(self, start_date: datetime, end_date: datetime, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search through conversations"""
        results = []
        keyword = options['keyword']
        file_extensions = options['file_extensions']
        show_content = options['show_content']
        case_sensitive = options['case_sensitive']
        
        # Create regex pattern
        if keyword:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(re.escape(keyword), flags)
        
        print(f"\n🔍 Searching conversations from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        if keyword:
            print(f"Keyword: '{keyword}' (case sensitive: {case_sensitive})")
        
        # Get conversation folders
        conv_folders = [f for f in self.history_path.iterdir() 
                       if f.is_dir() and start_date <= datetime.fromtimestamp(f.stat().st_mtime) <= end_date]
        
        print(f"Found {len(conv_folders)} conversation folders to search...")
        
        for conv_folder in sorted(conv_folders, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                # Read entries.json
                entries_file = conv_folder / "entries.json"
                if not entries_file.exists():
                    continue
                
                with open(entries_file, 'r', encoding='utf-8') as f:
                    entries_data = json.load(f)
                
                resource = entries_data.get('resource', '')
                if resource.startswith('file:///'):
                    resource = resource[8:].replace('%3A', ':')
                    resource = resource.replace('%20', ' ')
                
                # Search files in conversation
                matches = []
                all_files = [f for f in conv_folder.iterdir() if f.is_file()]
                
                for file_path in all_files:
                    # Filter by file extension
                    if file_extensions and file_path.suffix.lower() not in file_extensions:
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if keyword:
                            if pattern.search(content):
                                match_count = len(pattern.findall(content))
                                match_info = {
                                    'file': file_path.name,
                                    'extension': file_path.suffix,
                                    'matches': match_count,
                                    'size': len(content)
                                }
                                
                                if show_content:
                                    lines = content.split('\n')
                                    matching_lines = []
                                    for i, line in enumerate(lines):
                                        if pattern.search(line):
                                            start = max(0, i-2)
                                            end = min(len(lines), i+3)
                                            context = lines[start:end]
                                            matching_lines.append({
                                                'line_number': i+1,
                                                'context': context
                                            })
                                    match_info['content'] = matching_lines
                                
                                matches.append(match_info)
                        else:
                            # No keyword, just include file info
                            matches.append({
                                'file': file_path.name,
                                'extension': file_path.suffix,
                                'matches': 1,
                                'size': len(content)
                            })
                    
                    except Exception as e:
                        continue  # Skip files that can't be read
                
                if matches:
                    results.append({
                        'conversation_id': conv_folder.name,
                        'date': datetime.fromtimestamp(conv_folder.stat().st_mtime),
                        'resource': resource,
                        'file_count': len(all_files),
                        'matches': matches
                    })
            
            except Exception as e:
                continue  # Skip conversations that can't be read
        
        return results
    
    def display_results(self, results: List[Dict[str, Any]], options: Dict[str, Any]):
        """Display search results"""
        if not results:
            print("\n❌ No conversations found matching your criteria.")
            return
        
        total_matches = sum(len(conv['matches']) for conv in results)
        print(f"\n✅ Found {len(results)} conversations with {total_matches} total matches")
        print("=" * 80)
        
        for i, conv in enumerate(results, 1):
            print(f"\n📁 {i}. {conv['conversation_id']}")
            print(f"   📅 {conv['date'].strftime('%Y-%m-%d %H:%M')}")
            print(f"   📄 {conv['resource']}")
            print(f"   📊 {len(conv['matches'])} matching files")
            
            for match in conv['matches']:
                print(f"      🔍 {match['file']} ({match['extension']}) - {match['matches']} matches")
                
                if options['show_content'] and 'content' in match:
                    print("         Context:")
                    for content_match in match['content'][:3]:  # Show max 3 matches
                        print(f"         Line {content_match['line_number']}:")
                        for line in content_match['context']:
                            print(f"         {line}")
                        print()
    
    def interactive_search(self):
        """Main interactive search function"""
        print("🔍 Interactive Cursor Chat History Search Tool")
        print("=" * 50)
        
        if not self.validate_path():
            return
        
        while True:
            try:
                # Get date range
                start_date, end_date = self.get_date_range()
                
                # Get search options
                options = self.get_search_options()
                
                # Perform search
                results = self.search_conversations(start_date, end_date, options)
                
                # Display results
                self.display_results(results, options)
                
                # Ask if user wants to continue
                print("\n" + "=" * 80)
                continue_search = input("\nPerform another search? (y/N): ").strip().lower()
                if continue_search != 'y':
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 Search cancelled by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
        
        print("\n👋 Thanks for using the Chat History Search Tool!")

def main():
    """Main function"""
    searcher = CursorChatSearcher()
    searcher.interactive_search()

if __name__ == "__main__":
    main()
