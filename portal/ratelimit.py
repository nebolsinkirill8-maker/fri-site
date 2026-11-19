"""Fixed-window request limits kept in the shared database cache.

The database cache is shared by every application worker, so limits hold even
when the site runs several processes. Identifiers are hashed before they are
used in cache keys, so emails and IP addresses are not stored in plain text.
"""
import hashlib
import time

from django.conf import settings
from django.core.cache import cache

# (attempts, window in seconds)
LOGIN_PER_ACCOUNT = (5, 15 * 60)
LOGIN_PER_IP = (30, 15 * 60)
# Generous on purpose: a whole school class may register from one NAT address.
REGISTRATIONS_PER_IP = (20, 60 * 60)
TICKETS_PER_USER = (5, 60 * 60)

LOGIN_LOCKED_MESSAGE = 'Слишком много попыток входа. Подожди 15 минут и попробуй снова.'
REGISTRATION_LOCKED_MESSAGE = 'С этого адреса слишком много регистраций. Попробуй через час или напиши организаторам в Telegram.'
TICKETS_LOCKED_MESSAGE = 'Слишком много новых обращений за час. Допиши в уже открытое обращение или попробуй позже.'


def client_ip(request):
    # Only trust a forwarded header when settings name it; the proxy must overwrite it.
    header = settings.FRI_CLIENT_IP_HEADER
    forwarded = request.META.get(header, '') if header else ''
    return forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')


def _key(scope, identifier, window):
    digest = hashlib.sha256(str(identifier).encode()).hexdigest()[:32]
    return f'ratelimit:{scope}:{digest}:{int(time.time() // window)}'


def is_limited(scope, identifier, rule):
    limit, window = rule
    return cache.get(_key(scope, identifier, window), 0) >= limit


def hit(scope, identifier, rule):
    window = rule[1]
    key = _key(scope, identifier, window)
    cache.set(key, cache.get(key, 0) + 1, window)


def reset(scope, identifier, rule):
    cache.delete(_key(scope, identifier, rule[1]))
