#!/usr/bin/env python3
"""
API Authentication endpoints
"""
from flask import request, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app.models import User
from app import db
import logging

logger = logging.getLogger(__name__)

class AuthResource(Resource):
    """API Authentication endpoint"""
    
    def post(self):
        """Login and get access token"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'No data provided'}, 400
            
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return {'error': 'Email and password are required'}, 400
            
            # Find user
            user = User.query.filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                return {'error': 'Invalid credentials'}, 401
            
            if not user.active:
                return {'error': 'Account is disabled'}, 401
            
            # Create tokens
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(hours=24),
                additional_claims={
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.full_name
                }
            )
            
            refresh_token = create_refresh_token(
                identity=user.id,
                expires_delta=timedelta(days=30)
            )
            
            # Log successful login
            logger.info(f"API login successful for user: {user.email}")
            
            return {
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role
                },
                'expires_in': 24 * 3600  # 24 hours in seconds
            }, 200
            
        except Exception as e:
            logger.error(f"API login error: {str(e)}")
            return {'error': 'Internal server error'}, 500

class TokenRefreshResource(Resource):
    """Token refresh endpoint"""
    
    @jwt_required(refresh=True)
    def post(self):
        """Refresh access token"""
        try:
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.active:
                return {'error': 'User not found or disabled'}, 401
            
            # Create new access token
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(hours=24),
                additional_claims={
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.full_name
                }
            )
            
            return {
                'success': True,
                'access_token': access_token,
                'expires_in': 24 * 3600
            }, 200
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return {'error': 'Internal server error'}, 500

def admin_required(f):
    """Decorator to require admin role"""
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'admin':
            return {'error': 'Admin access required'}, 403
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current authenticated user"""
    current_user_id = get_jwt_identity()
    return User.query.get(current_user_id) if current_user_id else None
