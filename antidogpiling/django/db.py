from antidogpiling.django.common import Cache
from django.core.cache.backends import db


def CacheClass(table, params):
    """
    Database cache backend with support for anti-dogpiling. For Django 1.2.
    """

    return Cache(db.CacheClass, table, params)


def DatabaseCache(table, params):
    """
    Database cache backend with support for anti-dogpiling.
    """

    return Cache(db.DatabaseCache, table, params)
