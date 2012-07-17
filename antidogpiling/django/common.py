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

    def __init__(self, DjangoBackend, param, params):
        """
        Initialize with a Django cache backend. Example usage::

            from django.core.cache.backends import locmem
            cache = Cache(locmem.CacheClass, None, params)
        """

        super(Cache, self).__init__(**params)
        self._backend = DjangoBackend(param, params)

    def _set_directly(self, key, value, timeout, **kwargs):
        """
        Overriding as required by the AntiDogpiling class.
        """

        self._backend.set(key, value, timeout=timeout, **kwargs)

    def add(self, key, value, timeout=None, hard=False, grace_time=None,
            **kwargs):
        """
        Cache add with support for anti-dogpiling, enabled by default.
        """

        timeout = timeout or self.default_timeout

        if not hard:
            value, timeout = self._add_anti_dogpiling(value, timeout,
                                                      grace_time=grace_time)
        self._backend.add(key, value, timeout=timeout, **kwargs)

    def set(self, key, value, timeout=None, hard=False, grace_time=None,
            **kwargs):
        """
        Cache set with support for anti-dogpiling, enabled by default.
        """

        timeout = timeout or self.default_timeout

        if not hard:
            value, timeout = self._add_anti_dogpiling(value, timeout,
                                                      grace_time=grace_time)
        self._backend.set(key, value, timeout=timeout, **kwargs)

    def get(self, key, default=None, **kwargs):
        """
        Cache get with support for anti-dogpiling.
        """

        value = self._backend.get(key, **kwargs)
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
            value = self._backend.get(key, **kwargs)
            if self._is_anti_dogpiled(value):
                self._soft_invalidate(key, value, **kwargs)
                return

        self._backend.delete(key, **kwargs)

    def __getattr__(self, name):
        """
        Forward unrecognized attribute access (incr, decr, get_many, etc) to
        the backend.
        """

        return getattr(self._backend, name)

    def __contains__(self, key):
        """
        Forward any contains calls to the backend.
        """

        return key in self._backend
