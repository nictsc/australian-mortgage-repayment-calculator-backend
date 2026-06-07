import json
import requests
from django.conf import settings
from rest_framework import authentication, exceptions
from jose import jwt
from functools import lru_cache
from datetime import datetime, timedelta

from .models import User


class Auth0JWTAuthentication(authentication.BaseAuthentication):
    _jwks_cache = None
    _cache_expiry = None

    @classmethod
    def _get_jwks(cls, force_refresh=False):
        now = datetime.now()
        if force_refresh or cls._jwks_cache is None or (cls._cache_expiry and now > cls._cache_expiry):
            url = f'https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json'
            response = requests.get(url)
            response.raise_for_status()
            cls._jwks_cache = response.json()
            cls._cache_expiry = now + timedelta(seconds=300)
        return cls._jwks_cache

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode('utf-8')
        if not auth_header:
            return None

        try:
            auth_type, token = auth_header.split()
            if auth_type.lower() != 'bearer':
                return None
        except ValueError:
            raise exceptions.AuthenticationFailed('Invalid authorization header')

        try:
            jwks = self._get_jwks()
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = None

            for key in jwks.get('keys', []):
                if key.get('kid') == unverified_header.get('kid'):
                    rsa_key = key
                    break

            if not rsa_key:
                raise exceptions.AuthenticationFailed('Invalid token signature')

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=['RS256'],
                audience=settings.AUTH0_AUDIENCE,
                issuer=f'https://{settings.AUTH0_DOMAIN}/',
            )

            email = payload.get('email', '')
            # auth0 sub (e.g. "auth0|abc123") is globally unique — safe as username.
            username = payload['sub'][:150]
            user, _ = User.objects.get_or_create(
                auth0_id=payload['sub'],
                defaults={'email': email, 'username': username},
            )

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.JWTClaimsError:
            raise exceptions.AuthenticationFailed('Invalid token claims')
        except jwt.JWTError:
            raise exceptions.AuthenticationFailed('Invalid token')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
