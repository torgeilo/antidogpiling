from antidogpiling.django.common import Cache
from django.core.cache.backends import memcached


def CacheClass(server, params):
    """
    Memcached backend with support for anti-dogpiling. For Django 1.2.
    """

    return Cache(memcached.CacheClass, server, params)


def MemcachedCache(server, params):
    """
    Memcached backend with support for anti-dogpiling, using python-memcached.
    """

    return Cache(memcached.MemcachedCache, server, params)


def PyLibMCCache(server, params):
    """
    Memcached backend with support for anti-dogpiling, using pylibmc.
    """

    return Cache(memcached.PyLibMCCache, server, params)
