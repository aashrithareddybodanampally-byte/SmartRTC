#!/usr/bin/env python3
"""
Fix the authentication system in main.py by removing bcrypt dependency
"""

import re

def fix_authentication():
    # Read the original file
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Remove bcrypt import
    content = content.replace('from passlib.context import CryptContext', '# from passlib.context import CryptContext')
    
    # Remove pwd_context initialization
    content = re.sub(r'pwd_context = CryptContext\(.*?\)', '# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")', content, flags=re.DOTALL)
    
    # Replace users dictionary with plain text passwords
    users_pattern = r'"users": \{[^}]+\}'
    users_replacement = '''"users": {
        "admin": {"password": "admin123", "role": "admin"},
        "planner": {"password": "planner123", "role": "planner"},
        "viewer": {"password": "viewer123", "role": "viewer"}
    }'''
    content = re.sub(users_pattern, users_replacement, content, flags=re.DOTALL)
    
    # Replace hash_password function
    content = re.sub(r'def hash_password\(password: str\):\s*return pwd_context\.hash\(password\)', 
                     'def hash_password(password: str):\n    return password  # Plain text for demo', 
                     content, flags=re.DOTALL)
    
    # Replace verify_password function
    content = re.sub(r'def verify_password\(plain_password, hashed_password\):\s*return pwd_context\.verify\(plain_password, hashed_password\)', 
                     'def verify_password(plain_password, hashed_password):\n    return plain_password == hashed_password', 
                     content, flags=re.DOTALL)
    
    # Write the fixed content
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("Fixed authentication system - removed bcrypt dependency")

if __name__ == "__main__":
    fix_authentication()
