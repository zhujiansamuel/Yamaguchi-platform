"""
Custom authentication for data_aggregation app.
"""
import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class SimpleTokenAuthentication(authentication.BaseAuthentication):
    """
    Simple token authentication using BATCH_STATS_API_TOKEN.
    使用 BATCH_STATS_API_TOKEN 的简单 token 认证。

    Token should be passed in the Authorization header:
    Authorization: Bearer <token>
    
    This authentication uses the BATCH_STATS_API_TOKEN from settings
    for simple token-based authentication without JWT.
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        try:
            # Expected format: "Bearer <token>"
            parts = auth_header.split()

            if len(parts) != 2 or parts[0].lower() != 'bearer':
                raise exceptions.AuthenticationFailed('Invalid authorization header format')

            token = parts[1]

            # Get expected token from settings
            expected_token = getattr(settings, 'BATCH_STATS_API_TOKEN', '')

            if not expected_token or expected_token == 'change-this-to-a-secure-token':
                raise exceptions.AuthenticationFailed('API token not configured')

            if token != expected_token:
                raise exceptions.AuthenticationFailed('Invalid token')

            # Token is valid, return a tuple of (user, auth)
            return (None, {'token': token})

        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication error: {str(e)}')

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return 'Bearer'


class SimpleTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    OpenAPI schema extension for SimpleTokenAuthentication.
    用于 SimpleTokenAuthentication 的 OpenAPI schema 扩展。
    """
    target_class = 'apps.data_aggregation.authentication.SimpleTokenAuthentication'
    name = 'SimpleTokenAuthentication'

    def get_security_definition(self, auto_schema):
        """
        Define the security scheme for OpenAPI documentation.
        为 OpenAPI 文档定义安全方案。
        """
        return {
            'type': 'http',
            'scheme': 'bearer',
            'description': 'Simple token authentication using BATCH_STATS_API_TOKEN. Format: Bearer <token>'
        }


class QueryParamTokenAuthentication(authentication.BaseAuthentication):
    """
    Simple token authentication via query parameter.
    通过查询参数进行简单的 token 认证。

    Token should be passed as a query parameter:
    ?token=<token>
    """

    def authenticate(self, request):
        token = request.query_params.get('token', '')

        if not token:
            raise exceptions.AuthenticationFailed('Token is required')

        # Get expected token from settings
        expected_token = getattr(settings, 'BATCH_STATS_API_TOKEN', '')

        if not expected_token or expected_token == 'change-this-to-a-secure-token':
            raise exceptions.AuthenticationFailed('API token not configured')

        if token != expected_token:
            raise exceptions.AuthenticationFailed('Invalid token')

        # Token is valid, return a tuple of (user, auth)
        return (None, {'token': token})

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return 'Token'


class QueryParamTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    OpenAPI schema extension for QueryParamTokenAuthentication.
    用于 QueryParamTokenAuthentication 的 OpenAPI schema 扩展。
    """
    target_class = 'apps.data_aggregation.authentication.QueryParamTokenAuthentication'
    name = 'QueryParamTokenAuthentication'

    def get_security_definition(self, auto_schema):
        """
        Define the security scheme for OpenAPI documentation.
        为 OpenAPI 文档定义安全方案。
        """
        return {
            'type': 'apiKey',
            'in': 'query',
            'name': 'token',
            'description': 'API token passed as query parameter: ?token=<token>'
        }
