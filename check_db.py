#!/usr/bin/env python3
"""
Check Database Structure
"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database():
    """Check database structure"""
    
    # Check both database locations
    db_paths = ['claims.db', 'instance/claims.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f'📊 Found database: {db_path}')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = cursor.fetchall()
            print(f'   Tables: {[t[0] for t in tables]}')
            
            # Check claims table structure if exists
            if any('claims' in str(t) for t in tables):
                cursor.execute('PRAGMA table_info(claims)')
                columns = cursor.fetchall()
                print(f'   Claims columns: {[c[1] for c in columns]}')
                
                # Check if claim_type_id exists
                has_claim_type_id = any('claim_type_id' in str(c) for c in columns)
                print(f'   Has claim_type_id: {has_claim_type_id}')
            
            conn.close()
            print()

if __name__ == '__main__':
    check_database()