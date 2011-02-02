# -*- coding: utf-8 -*-

"""
Base functionality for anti-dogpiled caching.
"""


import time


__author__ = "Torgeir Lorange Østby"
__version__ = "1.0.1"
__docformat__ = "restructuredtext"


_now = lambda: int(time.time())
"""
Get the current absolute time in seconds since epoch.
"""


class Wrapper(object):
    """
    Wrapper for cached values with anti-dogpiling enabled.
    """

    def __init__(self, value, soft_timeout, hard_timeout, grace_time):
        """
        Set the values of the wrapper.

        :param value: The value to cache.
        :param soft_timeout: Absolute timestamp after which a new value should
                be produced.
        :param hard_timeout: The number of seconds until the value should
                disappear completely from the cache after it was last set or
                read. This should be much greater than the soft timeout.
        :param grace_time: The number of seconds a client is given to try to
                produce a new value after the current value has timed out. If
                the client fails to produce a new value within the grace
                period, a new client is given the chance for an equally long
                grace period.
        """

        self.value = value
        self.soft_timeout = soft_timeout
        self.hard_timeout = hard_timeout
        self.grace_time = grace_time


class AntiDogpiling(object):
    """
    Base class for anti-dogpiling.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the anti-dogpiling with base values.

        :param hard_timeout_factor: Multiplied with the soft timeout to
                produce the hard timeout. Default is 8, so if a value should be
                cached for 1 hour, it will actually stay in the cache for 8
                hours. See Wrapper.soft_timeout and Wrapper.hard_timeout for
                more information.
        :param default_grace_time: See Wrapper.grace_time. The default is 60
                seconds.
        """

        self.hard_timeout_factor = int(kwargs.pop("hard_timeout_factor", 8))
        self.default_grace_time = int(kwargs.pop("default_grace_time", 60))

    def _set_directly(self, key, value, timeout):
        """
        Method for setting a value directly in the cache. Must be implemented
        by the superclass. The implementation must not call any of the
        functions below or there will be corrupted values or endless recursion.
        
        Typical superclass implementation::

            def _set_directly(self, key, value, timeout):
                super(Cache, self).set(key, value, timeout)
        """

        raise NotImplementedError()

    def _add_anti_dogpiling(self, value, timeout, grace_time=None):
        """
        Add a wrapper around the value with data needed later by the
        anti-dogpiling mechanisms. A new value and timeout is returned.

        :param value: A value to cache.
        :param timeout: The number of seconds the value should be cached
                before a new value should be produced.
        :param grace_time: See Wrapper.grace_time. If not specified, the
                default grace time is used.

        Use this function before putting the value into the cache::

            if use_anti_dogpiling:
                value, timeout = self._add_anti_dogpiling(value, timeout)
                self.set(key, value, timeout=timeout)
        """

        soft_timeout = timeout + _now()
        hard_timeout = timeout * self.hard_timeout_factor
        grace_time = grace_time or self.default_grace_time

        wrapped_value = Wrapper(value, soft_timeout, hard_timeout, grace_time)

        return wrapped_value, hard_timeout

    def _is_anti_dogpiled(self, value):
        """
        Check if the given value is wrapped in an anti-dogpiling wrapper. Use
        it when fetching values from the cache::

            if self._is_anti_dogpiled(value):
                value = self._apply_anti_dogpiling(key, value)
                return value
        """

        return isinstance(value, Wrapper)

    def _apply_anti_dogpiling(self, key, value):
        """
        Apply the anti-dogpiling mechanisms to the provided key and value. Use
        this when fetching values from the cache::

            if self._is_anti_dogpiled(value):
                value = self._apply_anti_dogpiling(key, value)
                return value
        """

        now = _now()

        # If no timeout, just return the value
        if value.soft_timeout >= now:
            return value.value

        # We have a soft timeout. The client gets the grace period to produce
        # and set an updated value while everyone else gets the old value.
        value.soft_timeout = now + value.grace_time
        self._set_directly(key, value, value.hard_timeout)

        return None

    def _soft_invalidate(self, key, value):
        """
        Invalidate an anti-dogpiled value while keeping the properties of
        anti-dogpiling. Example usage::

            if self._is_anti_dogpiled(value):
                self._soft_invalidate(key, value)
        """

        value.soft_timeout = 0
        self._set_directly(key, value, value.hard_timeout)
