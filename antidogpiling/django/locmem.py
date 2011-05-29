from antidogpiling.django.common import Cache
from django.core.cache.backends import locmem


def CacheClass(_, params):
    """
    In-memory cache backend with support for anti-dogpiling. For Django 1.2.
    """

    return Cache(locmem.CacheClass, _, params)


def LocMemCache(name, params):
    """
    In-memory cache backend with support for anti-dogpiling.
    """

    return Cache(locmem.LocMemCache, name, params)
