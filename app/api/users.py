#!/usr/bin/env python3
"""
API endpoints for users management (admin only)
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from datetime import datetime
from app.models import User
from app.api.auth import get_current_user, admin_required
from app import db
import logging

logger = logging.getLogger(__name__)

class UsersResource(Resource):
    """Users collection endpoint (admin only)"""
    
    @jwt_required()
    @admin_required
    def get(self):
        """Get list of users"""
        try:
            # Parse query parameters
            active_only = request.args.get('active_only', 'false').lower() == 'true'
            role = request.args.get('role')
            
            query = User.query
            
            if active_only:
                query = query.filter(User.active == True)
            
            if role:
                query = query.filter(User.role == role)
            
            users = query.order_by(User.created_at.desc()).all()
            
            users_list = []
            for user in users:
                users_list.append({
                    'id': user.id,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role,
                    'active': user.active,
                    'created_at': user.created_at.isoformat(),
                    'claims_count': len(user.claims)
                })
            
            return {
                'success': True,
                'users': users_list,
                'total': len(users_list)
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    @admin_required
    def post(self):
        """Create new user"""
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Validate required fields
            required_fields = ['full_name', 'email', 'password', 'role']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400
            
            # Validate role
            valid_roles = ['admin', 'claims_agent', 'viewer']
            if data['role'] not in valid_roles:
                return {'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}, 400
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return {'error': 'User with this email already exists'}, 409
            
            # Create user
            user = User(
                full_name=data['full_name'],
                email=data['email'],
                role=data['role'],
                active=data.get('active', True)
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User created via API: {user.email}")
            
            return {
                'success': True,
                'user_id': user.id,
                'message': 'User created successfully'
            }, 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return {'error': 'Internal server error'}, 500

class UserResource(Resource):
    """Individual user endpoint (admin only)"""
    
    @jwt_required()
    @admin_required
    def get(self, user_id):
        """Get specific user details"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'full_name': user.full_name,
                    'email': user.email,
                    'role': user.role,
                    'active': user.active,
                    'created_at': user.created_at.isoformat(),
                    'claims_count': len(user.claims),
                    'recent_claims': [
                        {
                            'id': claim.id,
                            'client_name': claim.client_name,
                            'claim_amount': float(claim.claim_amount),
                            'status': claim.status,
                            'created_at': claim.created_at.isoformat()
                        } for claim in user.claims[-5:]  # Last 5 claims
                    ]
                }
            }, 200
            
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    @admin_required
    def put(self, user_id):
        """Update user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            # Update allowed fields
            if 'full_name' in data:
                user.full_name = data['full_name']
            
            if 'email' in data:
                # Check if email is already taken by another user
                existing_user = User.query.filter(
                    User.email == data['email'],
                    User.id != user_id
                ).first()
                if existing_user:
                    return {'error': 'Email already taken by another user'}, 409
                user.email = data['email']
            
            if 'role' in data:
                valid_roles = ['admin', 'claims_agent', 'viewer']
                if data['role'] not in valid_roles:
                    return {'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}, 400
                user.role = data['role']
            
            if 'active' in data:
                user.active = data['active']
            
            if 'password' in data:
                user.set_password(data['password'])
            
            db.session.commit()
            
            logger.info(f"User updated via API: {user.email}")
            
            return {
                'success': True,
                'message': 'User updated successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
    
    @jwt_required()
    @admin_required
    def delete(self, user_id):
        """Delete user"""
        try:
            current_user = get_current_user()
            
            # Prevent self-deletion
            if current_user.id == user_id:
                return {'error': 'Cannot delete your own account'}, 409
            
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404
            
            # Check if user has claims
            if user.claims:
                return {'error': 'Cannot delete user with existing claims. Deactivate instead.'}, 409
            
            user_email = user.email
            db.session.delete(user)
            db.session.commit()
            
            logger.info(f"User deleted via API: {user_email}")
            
            return {
                'success': True,
                'message': 'User deleted successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return {'error': 'Internal server error'}, 500
