from antidogpiling.django.common import Cache
from django.core.cache.backends import memcached


def CacheClass(server, params):
    """
    Memcached backend with support for anti-dogpiling.
    """

    return Cache(memcached.CacheClass, server, params)
