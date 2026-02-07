#!/usr/bin/env python3
"""
Cookie Import Script for StreamCapOrigin

This script converts browser-exported cookies (JSON format) to the application's cookie format.
It can be used to update TikTok cookies for the StreamCapOrigin application.

Usage:
    python import_cookies.py [source_file] [target_file]
    
Arguments:
    source_file: Path to the exported cookies JSON file (default: browser-exported file path)
    target_file: Path to the application's cookies.json file (default: ./config/cookies.json)

Example:
    python import_cookies.py "C:\\Users\\Test\\Videos\\Disco\\R\\www.tiktok.com.cookies.json"
"""

import json
import os
import sys
from datetime import datetime



from app.utils.cookie_importer import load_json_cookies, convert_json_to_cookie_string


def load_app_cookies(file_path):
    """
    Load the application's existing cookies configuration.
    
    Args:
        file_path (str): Path to the application's cookies.json file
        
    Returns:
        dict: Current cookies configuration
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Application cookies file not found: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in application cookies file: {e}")
        return {}
    except Exception as e:
        print(f"Error reading application cookies file: {e}")
        return {}


def save_app_cookies(file_path, cookies_config):
    """
    Save the updated cookies configuration to the application's file.
    
    Args:
        file_path (str): Path to the application's cookies.json file
        cookies_config (dict): Updated cookies configuration
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cookies_config, f, indent=4, ensure_ascii=False)
        
        print(f"✓ Cookies successfully saved to: {file_path}")
        
    except Exception as e:
        print(f"Error saving cookies: {e}")


def create_backup(file_path):
    """
    Create a backup of the existing cookies file.
    
    Args:
        file_path (str): Path to the file to backup
    """
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as src, \
                 open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            print(f"✓ Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return None
    
    return None


def main():
    """Main function to handle cookie import."""
    
    # Default paths
    default_source = r"C:\Users\Test\Videos\Disco\R\www.tiktok.com.cookies.json"
    default_target = r"E:\dev\StreamCapOrigin\config\cookies.json"
    
    # Parse command line arguments
    source_file = sys.argv[1] if len(sys.argv) > 1 else default_source
    target_file = sys.argv[2] if len(sys.argv) > 2 else default_target
    
    print("🔥 StreamCapOrigin Cookie Import Tool 🔥")
    print("=" * 50)
    print(f"Source file: {source_file}")
    print(f"Target file: {target_file}")
    print()
    
    # Load browser-exported cookies
    print("📥 Loading browser-exported cookies...")
    cookies_json = load_json_cookies(source_file)
    
    if not cookies_json:
        print("❌ No cookies found or failed to load cookies from source file.")
        return 1
    
    print(f"✓ Loaded {len(cookies_json)} cookies from browser export")
    
    # Convert to cookie string format
    print("🔄 Converting cookies to application format...")
    cookie_string = convert_json_to_cookie_string(cookies_json)
    
    if not cookie_string:
        print("❌ Failed to convert cookies to string format.")
        return 1
    
    print(f"✓ Converted to cookie string ({len(cookie_string)} characters)")
    
    # Load existing application cookies
    print("📂 Loading existing application cookies...")
    app_cookies = load_app_cookies(target_file)
    
    # Create backup
    print("💾 Creating backup of existing cookies...")
    backup_path = create_backup(target_file)
    
    # Update the tiktok cookies
    app_cookies['tiktok'] = cookie_string
    
    # Save updated cookies
    print("💾 Saving updated cookies...")
    save_app_cookies(target_file, app_cookies)
    
    print()
    print("🎉 Cookie import completed successfully!")
    print(f"✓ {len(cookies_json)} cookies imported")
    print(f"✓ TikTok cookies updated in: {target_file}")
    if backup_path:
        print(f"✓ Backup saved as: {backup_path}")
    
    # Show some cookie info
    cookie_names = [cookie.get('name', 'unnamed') for cookie in cookies_json[:10]]
    print(f"✓ Cookie preview: {', '.join(cookie_names)}...")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Import cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
