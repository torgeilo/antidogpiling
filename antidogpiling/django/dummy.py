from antidogpiling.django.common import Cache
from django.core.cache.backends import dummy


class BaseDummyCache(Cache):
    """
    Dummy implementations of incr and decr, as the same methods in
    django.core.cache.base.BaseCache do not work with dummy add and set
    methods.
    """

    def incr(self, key, delta=1, **kwargs):
        return 1

    def decr(self, key, delta=1, **kwargs):
        return 0


def CacheClass(host, *args, **kwargs):
    """
    Dummy backend for Django 1.2. Use this when you need a dummy backend with
    support for cache method arguments like hard=True.
    """

    return BaseDummyCache(dummy.CacheClass, host, *args, **kwargs)


def DummyCache(host, *args, **kwargs):
    """
    Dummy backend. Use this when you need a dummy backend with support for
    cache method arguments like hard=True.
    """

    return BaseDummyCache(dummy.DummyCache, host, *args, **kwargs)
