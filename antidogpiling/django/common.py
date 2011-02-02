from antidogpiling import AntiDogpiling


class Cache(AntiDogpiling):
    """
    Django cache backend with support for anti-dogpiling. Get many, set many,
    delete many, incr, and decr are not anti-dogpile enabled, but can be used
    as long as they are not used on anti-dogpiled values.
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

    def _set_directly(self, key, value, timeout):
        """
        Overriding as required by subclass.
        """

        super(Cache, self).set(key, value, timeout=timeout)

    def add(self, key, value, timeout=None, hard=False, grace_time=None):
        """
        Cache add with support for anti-dogpiling, enabled by default.
        """

        timeout = timeout or self.default_timeout

        if not hard:
            value, timeout = self._add_anti_dogpiling(value, timeout,
                                                      grace_time=grace_time)
        super(Cache, self).add(key, value, timeout=timeout)

    def set(self, key, value, timeout=None, hard=False, grace_time=None):
        """
        Cache set with support for anti-dogpiling, enabled by default.
        """

        timeout = timeout or self.default_timeout

        if not hard:
            value, timeout = self._add_anti_dogpiling(value, timeout,
                                                      grace_time=grace_time)
        super(Cache, self).set(key, value, timeout=timeout)

    def get(self, key, default=None):
        """
        Cache get with support for anti-dogpiling.
        """

        value = super(Cache, self).get(key)
        if self._is_anti_dogpiled(value):
            value = self._apply_anti_dogpiling(key, value)
        if value is None:
            return default
        return value

    def delete(self, key, hard=False):
        """
        Cache delete with support for anti-dogpiling (soft invalidation),
        enabled by default.
        """

        if not hard:
            value = super(Cache, self).get(key)
            if self._is_anti_dogpiled(value):
                self._soft_invalidate(key, value)
                return

        super(Cache, self).delete(key)
