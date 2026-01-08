from app.utils.i18n import load_translations, tr

def test_i18n():
    # Mock translations
    translations = {
        "console": {
            "hello": "Hello World",
            "nested": {
                "key": "Nested Value"
            },
            "format_str": "Value: {}"
        }
    }
    
    load_translations(translations)
    
    # Test simple key
    assert tr("console.hello") == "Hello World"
    print("Test 1 Passed: Simple key")
    
    # Test formatted string
    assert tr("console.format_str").format(123) == "Value: 123"
    print("Test 2 Passed: Formatted string")
    
    # Test missing key with default
    assert tr("console.missing", "Default") == "Default"
    print("Test 3 Passed: Missing key with default")
    
    # Test missing key without default
    assert tr("console.missing_no_default") == "console.missing_no_default"
    print("Test 4 Passed: Missing key without default")

if __name__ == "__main__":
    try:
        test_i18n()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
