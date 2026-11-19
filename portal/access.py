"""Private preview: the whole site answers 404 until the visitor opens the invite link.

The invite link is /invite/<DJANGO_ACCESS_KEY>/. It sets a signed cookie and redirects
to the home page, so the key does not stay in the address bar or the Referer header.
Changing the key revokes every cookie issued for the old one. With an empty key the
gate is off (local development).
"""
import hashlib
import hmac

from django.conf import settings
from django.core import signing
from django.http import HttpResponseNotFound, HttpResponseRedirect

COOKIE_NAME = 'fri_access'
COOKIE_SALT = 'fri.access-gate'
COOKIE_MAX_AGE = 90 * 24 * 60 * 60
INVITE_PREFIX = '/invite/'
# Deliberately bare: unauthorized visitors should not learn what is hosted here.
NOT_FOUND_BODY = '<!doctype html><title>Not Found</title><h1>Not Found</h1>'


def _fingerprint(key):
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def _has_access(request, key):
    try:
        value = request.get_signed_cookie(COOKIE_NAME, salt=COOKIE_SALT, max_age=COOKIE_MAX_AGE)
    except (KeyError, signing.BadSignature):
        return False
    return hmac.compare_digest(value, _fingerprint(key))


class AccessGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        key = settings.FRI_ACCESS_KEY
        if not key:
            return self.get_response(request)
        if request.path.startswith(INVITE_PREFIX):
            response = self._invite(request, key)
        elif _has_access(request, key):
            response = self.get_response(request)
        else:
            response = HttpResponseNotFound(NOT_FOUND_BODY)
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response

    def _invite(self, request, key):
        supplied = request.path[len(INVITE_PREFIX):].strip('/')
        if not hmac.compare_digest(supplied.encode(), key.encode()):
            return HttpResponseNotFound(NOT_FOUND_BODY)
        response = HttpResponseRedirect('/')
        response.set_signed_cookie(
            COOKIE_NAME, _fingerprint(key), salt=COOKIE_SALT, max_age=COOKIE_MAX_AGE,
            secure=settings.SESSION_COOKIE_SECURE, httponly=True, samesite='Lax',
        )
        return response
