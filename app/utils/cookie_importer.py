
import json

def convert_json_to_cookie_string(cookies_json):
    """
    Convert browser-exported JSON cookies to cookie string format.
    
    Args:
        cookies_json (list): List of cookie objects from browser export
        
    Returns:
        str: Formatted cookie string for the application
    """
    cookie_parts = []
    
    for cookie in cookies_json:
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        if name and value:
            cookie_parts.append(f"{name}={value}")
    
    return '; '.join(cookie_parts)


def load_json_cookies(file_path):
    """
    Load cookies from JSON file.
    
    Args:
        file_path (str): Path to the JSON cookies file
        
    Returns:
        list: List of cookie objects
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        if isinstance(cookies, list):
            return cookies
        else:
            print(f"Error: Expected a list of cookies, got {type(cookies)}")
            return []
            
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error reading cookies file: {e}")
        return []
