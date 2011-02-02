from antidogpiling.django.common import Cache
from django.core.cache.backends import locmem


def CacheClass(_, params):
    """
    In-memory cache backend with support for anti-dogpiling.
    """

    return Cache(locmem.CacheClass, _, params)
