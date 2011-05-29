from antidogpiling import AntiDogpiling


class Cache(AntiDogpiling):
    """
    Generic Django cache backend with support for anti-dogpiling. The actual
    Django cache backend is inserted as a dynamic mixin. In this way, no Django
    code needs to be re-implmeneted.

    Get many, set many, and delete many are not anti-dogpilie enabled here (did
    not bother), but they can be used as long as they are not used on
    anti-dogpiled values.

    If incr and decr were anti-dogpilied one would loose the atomic properties
    of these in Memcached.
    """

    def __init__(self, CacheClass, param, params):
        """
        Initialize with a Django cache backend as mixin. Example usage::

            from django.core.cache.backends import locmem
            cache = Cache(locmem.CacheClass, None, params)
        """

        # Add mixin
        if CacheClass not in Cache.__bases__:
            if len(Cache.__bases__) > 1:
                raise RuntimeError("Already mixed")
            Cache.__bases__ += (CacheClass,)

        # Initialize subclasses
        AntiDogpiling.__init__(self, **params)
        CacheClass.__init__(self, param, params)

    def _set_directly(self, key, value, timeout, **kwargs):
        """
        Overriding as required by the AntiDogpiling class.
        """

        super(Cache, self).set(key, value, timeout=timeout, **kwargs)

    def add(self, key, value, timeout=None, hard=False, grace_time=None,
            **kwargs):
        """
        Cache add with support for anti-dogpiling, enabled by default.
        """

        timeout = timeout or self.default_timeout

        if not hard:
            value, timeout = self._add_anti_dogpiling(value, timeout,
                                                      grace_time=grace_time)
        super(Cache, self).add(key, value, timeout=timeout, **kwargs)

    def set(self, key, value, timeout=None, hard=False, grace_time=None,
            **kwargs):
        """
        Cache set with support for anti-dogpiling, enabled by default.
        """

        timeout = timeout or self.default_timeout

        if not hard:
            value, timeout = self._add_anti_dogpiling(value, timeout,
                                                      grace_time=grace_time)
        super(Cache, self).set(key, value, timeout=timeout, **kwargs)

    def get(self, key, default=None, **kwargs):
        """
        Cache get with support for anti-dogpiling.
        """

        value = super(Cache, self).get(key, **kwargs)
        if self._is_anti_dogpiled(value):
            value = self._apply_anti_dogpiling(key, value, **kwargs)
        if value is None:
            return default
        return value

    def delete(self, key, hard=False, **kwargs):
        """
        Cache delete with support for anti-dogpiling (soft invalidation),
        enabled by default.
        """

        if not hard:
            value = super(Cache, self).get(key, **kwargs)
            if self._is_anti_dogpiled(value):
                self._soft_invalidate(key, value, **kwargs)
                return

        super(Cache, self).delete(key, **kwargs)
