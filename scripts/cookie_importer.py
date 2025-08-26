#!/usr/bin/env python3
"""
Universal Cookie Importer for StreamCapOrigin

A standalone utility to import browser-exported cookies into the StreamCapOrigin application.
Supports various cookie export formats and provides flexible configuration options.

Features:
- Converts JSON cookie exports to application format
- Automatic backup of existing cookies
- Support for custom file paths
- Interactive mode for guided imports
- Validation of cookie formats
- Detailed logging and progress reporting

Usage:
    # Interactive mode (recommended)
    python cookie_importer.py
    
    # Command line mode
    python cookie_importer.py --source "path/to/cookies.json" --target "path/to/app/cookies.json"
    
    # Quick import with defaults
    python cookie_importer.py --quick
    
    # Help
    python cookie_importer.py --help

Author: StreamCapOrigin Project
Version: 1.0.0
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path


class CookieImporter:
    """Main class for handling cookie imports."""
    
    def __init__(self):
        self.verbose = True
        self.created_backup = False
        
    def log(self, message, level="INFO"):
        """Print log messages with formatting."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            icons = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROGRESS": "🔄"}
            icon = icons.get(level, "•")
            print(f"{icon} [{timestamp}] {message}")
    
    def validate_json_cookies(self, cookies_data):
        """Validate the structure of imported cookies."""
        if not isinstance(cookies_data, list):
            return False, "Expected a list of cookie objects"
        
        required_fields = ['name', 'value']
        for i, cookie in enumerate(cookies_data):
            if not isinstance(cookie, dict):
                return False, f"Cookie at index {i} is not a dictionary"
            
            for field in required_fields:
                if field not in cookie:
                    return False, f"Cookie at index {i} missing required field: {field}"
        
        return True, "Valid cookie structure"
    
    def convert_cookies_to_string(self, cookies_list):
        """Convert list of cookie objects to application cookie string format."""
        cookie_pairs = []
        
        for cookie in cookies_list:
            name = str(cookie.get('name', '')).strip()
            value = str(cookie.get('value', '')).strip()
            
            if name and value:
                # Handle special characters in cookie values
                cookie_pairs.append(f"{name}={value}")
        
        return '; '.join(cookie_pairs)
    
    def load_cookies_from_file(self, file_path):
        """Load cookies from a JSON file with error handling."""
        try:
            file_path = Path(file_path).resolve()
            
            if not file_path.exists():
                raise FileNotFoundError(f"Cookie file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            is_valid, message = self.validate_json_cookies(data)
            if not is_valid:
                raise ValueError(f"Invalid cookie format: {message}")
            
            return data, None
        
        except FileNotFoundError as e:
            return None, str(e)
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, f"Error loading cookies: {e}"
    
    def load_app_config(self, config_path):
        """Load existing application cookie configuration."""
        try:
            config_path = Path(config_path).resolve()
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.log("Application config file not found, creating new one", "WARNING")
                return {}
        
        except json.JSONDecodeError as e:
            self.log(f"Invalid JSON in config file, creating backup and starting fresh: {e}", "WARNING")
            return {}
        except Exception as e:
            self.log(f"Error loading app config: {e}", "WARNING")
            return {}
    
    def create_backup(self, file_path):
        """Create a timestamped backup of existing files."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f".backup_{timestamp}.json")
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            self.created_backup = True
            self.log(f"Backup created: {backup_path.name}", "SUCCESS")
            return backup_path
            
        except Exception as e:
            self.log(f"Could not create backup: {e}", "WARNING")
            return None
    
    def save_app_config(self, config_path, config_data):
        """Save updated configuration to file."""
        try:
            config_path = Path(config_path).resolve()
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            return True, None
            
        except Exception as e:
            return False, f"Error saving configuration: {e}"
    
    def interactive_import(self):
        """Interactive mode for guided cookie import."""
        print("\n" + "=" * 60)
        print("🍪 Interactive Cookie Import for StreamCapOrigin 🍪")
        print("=" * 60)
        
        # Get source file
        default_source = r"C:\Users\Test\Videos\Disco\R\www.tiktok.com.cookies.json"
        print(f"\n1. Source Cookie File")
        print(f"   Default: {default_source}")
        source_input = input("   Enter path (or press Enter for default): ").strip()
        source_file = source_input if source_input else default_source
        
        if not Path(source_file).exists():
            print(f"❌ Source file not found: {source_file}")
            print("   Please check the path and try again.")
            return False
        
        # Get target file
        script_dir = Path(__file__).parent.parent
        default_target = script_dir / "config" / "cookies.json"
        print(f"\n2. Target Application Config")
        print(f"   Default: {default_target}")
        target_input = input("   Enter path (or press Enter for default): ").strip()
        target_file = target_input if target_input else str(default_target)
        
        # Confirmation
        print(f"\n3. Import Summary")
        print(f"   Source: {source_file}")
        print(f"   Target: {target_file}")
        
        confirm = input("\n   Proceed with import? [Y/n]: ").strip().lower()
        if confirm and confirm != 'y' and confirm != 'yes':
            print("❌ Import cancelled.")
            return False
        
        # Perform import
        return self.import_cookies(source_file, target_file)
    
    def import_cookies(self, source_path, target_path):
        """Main import function."""
        self.log("Starting cookie import process", "PROGRESS")
        
        # Load source cookies
        self.log("Loading source cookies...", "PROGRESS")
        cookies_data, error = self.load_cookies_from_file(source_path)
        
        if error:
            self.log(f"Failed to load source cookies: {error}", "ERROR")
            return False
        
        self.log(f"Loaded {len(cookies_data)} cookies from source", "SUCCESS")
        
        # Convert cookies
        self.log("Converting cookies to application format...", "PROGRESS")
        cookie_string = self.convert_cookies_to_string(cookies_data)
        
        if not cookie_string:
            self.log("No valid cookies found to convert", "ERROR")
            return False
        
        self.log(f"Converted to cookie string ({len(cookie_string)} characters)", "SUCCESS")
        
        # Load existing config
        self.log("Loading existing application configuration...", "PROGRESS")
        app_config = self.load_app_config(target_path)
        
        # Create backup
        self.log("Creating backup of existing configuration...", "PROGRESS")
        backup_path = self.create_backup(target_path)
        
        # Update configuration
        app_config['tiktok'] = cookie_string
        
        # Save updated config
        self.log("Saving updated configuration...", "PROGRESS")
        success, error = self.save_app_config(target_path, app_config)
        
        if not success:
            self.log(f"Failed to save configuration: {error}", "ERROR")
            return False
        
        # Success summary
        print("\n" + "=" * 50)
        self.log("Cookie import completed successfully!", "SUCCESS")
        self.log(f"Imported {len(cookies_data)} cookies", "SUCCESS")
        self.log(f"Updated: {target_path}", "SUCCESS")
        
        if backup_path:
            self.log(f"Backup: {backup_path.name}", "SUCCESS")
        
        # Show sample cookies
        sample_cookies = [c.get('name', 'unnamed') for c in cookies_data[:5]]
        self.log(f"Sample cookies: {', '.join(sample_cookies)}...", "INFO")
        
        return True


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Import browser-exported cookies into StreamCapOrigin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\nExamples:
  Interactive mode:
    python cookie_importer.py
  
  Command line mode:
    python cookie_importer.py --source cookies.json --target config/cookies.json
  
  Quick import with defaults:
    python cookie_importer.py --quick
        """
    )
    
    parser.add_argument(
        '--source', '-s',
        help='Path to the exported cookies JSON file'
    )
    
    parser.add_argument(
        '--target', '-t',
        help='Path to the application cookies configuration file'
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Quick import using default paths'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Cookie Importer v1.0.0'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    importer = CookieImporter()
    importer.verbose = not args.quiet
    
    # Handle different modes
    if args.quick:
        # Quick mode with defaults
        default_source = r"C:\Users\Test\Videos\Disco\R\www.tiktok.com.cookies.json"
        script_dir = Path(__file__).parent.parent
        default_target = script_dir / "config" / "cookies.json"
        
        if importer.verbose:
            print("🚀 Quick import mode")
            print(f"Source: {default_source}")
            print(f"Target: {default_target}")
        
        return importer.import_cookies(default_source, str(default_target))
    
    elif args.source or args.target:
        # Command line mode
        if not args.source:
            print("❌ Error: --source is required when using command line mode")
            return False
        
        if not args.target:
            script_dir = Path(__file__).parent.parent
            args.target = str(script_dir / "config" / "cookies.json")
        
        return importer.import_cookies(args.source, args.target)
    
    else:
        # Interactive mode (default)
        return importer.interactive_import()


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Import cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
