from antidogpiling.django.common import Cache
from django.core.cache.backends import db


def CacheClass(table, params):
    """
    Database cache backend with support for anti-dogpiling.
    """

    return Cache(db.CacheClass, table, params)
