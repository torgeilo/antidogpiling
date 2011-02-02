from antidogpiling.django.common import Cache
from django.core.cache.backends import filebased


def CacheClass(directory, params):
    """
    File-based cache backend with support for anti-dogpiling.
    """

    return Cache(filebased.CacheClass, directory, params)
