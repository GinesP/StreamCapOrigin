from typing import Dict, Any

_translations: Dict[str, Any] = {}


def load_translations(new_translations: Dict[str, Any]) -> None:
    """
    Load new translations into the global dictionary.
    
    Args:
        new_translations: Dictionary containing translation key-value pairs
    """
    global _translations
    _translations = new_translations


def tr(key: str, default: str = None) -> str:
    """
    Get translated string for a key.
    
    Args:
        key: Dot-separated key (e.g., 'console.started_recording')
        default: Default text to return if key not found
        
    Returns:
        Translated string or default/key
    """
    try:
        keys = key.split('.')
        value = _translations
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default or key
                
        if value is None:
            return default or key
            
        return str(value)
    except Exception:
        return default or key
