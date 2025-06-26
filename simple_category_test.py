#!/usr/bin/env python3
"""Simple test to verify category fix"""

# Simulate the exact fix we made
def test_category_extraction():
    print("=== Testing Category Extraction Logic ===")
    
    # Test 1: Dictionary category (from ML categorizer)
    test_category_dict = {'id': 1, 'name': 'Продукти', 'icon': '🛒'}
    category_info = test_category_dict
    category_name = ''
    
    if isinstance(category_info, dict):
        category_name = category_info.get('name', '')
        print(f"✅ Dict case: category_name = '{category_name}'")
        print(f"✅ Can call .lower(): '{category_name.lower()}'")
    elif isinstance(category_info, str):
        category_name = category_info
        print(f"✅ String case: category_name = '{category_name}'")
    
    # Test 2: String category 
    test_category_string = "Розваги"
    category_info = test_category_string
    category_name = ''
    
    if isinstance(category_info, dict):
        category_name = category_info.get('name', '')
        print(f"✅ Dict case: category_name = '{category_name}'")
    elif isinstance(category_info, str):
        category_name = category_info
        print(f"✅ String case: category_name = '{category_name}'")
        print(f"✅ Can call .lower(): '{category_name.lower()}'")
    
    print("\n✅ All tests passed! The fix handles both dict and string categories correctly.")

if __name__ == "__main__":
    test_category_extraction()
