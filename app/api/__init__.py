#!/usr/bin/env python3
"""
API module for external integrations
"""
from flask import Blueprint
from flask_restful import Api

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(api_bp)

# Import and register API resources
from .auth import AuthResource, TokenRefreshResource
from .claims import ClaimsResource, ClaimResource, ClaimStatusResource
from .companies import CompaniesResource, CompanyResource
from .reports import ReportsResource, AnalyticsResource
from .users import UsersResource, UserResource

# Authentication endpoints
api.add_resource(AuthResource, '/auth/login')
api.add_resource(TokenRefreshResource, '/auth/refresh')

# Claims endpoints
api.add_resource(ClaimsResource, '/claims')
api.add_resource(ClaimResource, '/claims/<string:claim_id>')
api.add_resource(ClaimStatusResource, '/claims/<string:claim_id>/status')

# Companies endpoints
api.add_resource(CompaniesResource, '/companies')
api.add_resource(CompanyResource, '/companies/<int:company_id>')

# Reports endpoints
api.add_resource(ReportsResource, '/reports')
api.add_resource(AnalyticsResource, '/analytics')

# Users endpoints (admin only)
api.add_resource(UsersResource, '/users')
api.add_resource(UserResource, '/users/<int:user_id>')
