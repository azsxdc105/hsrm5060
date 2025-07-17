#!/usr/bin/env python3
"""
Main application runner for the Insurance Claims Management System
"""
import os
from app import create_app, db
from app.models import User, InsuranceCompany, Claim, ClaimAttachment, EmailLog, SystemSettings
from flask_migrate import upgrade

def deploy():
    """Run deployment tasks."""
    app = create_app()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Run database migrations
        try:
            upgrade()
        except:
            pass

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'InsuranceCompany': InsuranceCompany,
        'Claim': Claim,
        'ClaimAttachment': ClaimAttachment,
        'EmailLog': EmailLog,
        'SystemSettings': SystemSettings
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)