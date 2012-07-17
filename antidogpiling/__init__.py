# -*- coding: utf-8 -*-
"""
Base functionality for anti-dogpiled caching.

Make anti-dogpiled cache implementations by subclassing the AntiDogpiling class
and using its methods. A basic example with no options or validity checks::

    class Cache(AntiDogpiling):
        def __init__(self, connector):
            self.connector = connector

        def _set_directly(self, key, value, timeout):
            self.connector.set(key, value, timeout)

        def set(self, key, value, timeout):
            value, timeout = self._add_anti_dogpiling(value, timeout)
            self.connector.set(key, value, timeout)

        def get(self, key):
            value = self.connector.get(key)
            if value is not None:
                value = self._apply_anti_dogpiling(key, value)
            return value

        def delete(self, key):
            value = self.connector.get(key)
            if value is not None:
                self._soft_invalidate(key, value)

By using the _is_anti_dogpiled(value) function it is possible to make the anti-
dogpiling optional, per value. For example (showing the relevant methods
only)::

    ...
        def set(self, key, value, timeout, adp=True):
            if adp:
                value, timeout = self._add_anti_dogpiling(value, timeout)
            self.connector.set(key, value, timeout)

        def get(self, key):
            value = self.connector.get(key)
            if self._is_anti_dogpiled(value):
                value = self._apply_anti_dogpiling(key, value)
            return value

        def delete(self, key, adp=True):
            if adp:
                value = self.connector.get(key)
                if self._is_anti_dogpiled(value):
                    self._soft_invalidate(key, value)
                    return
            connector.delete(key)
    ...

All timeout values provided to the anti-dogpiling methods must be relative and
in seconds. Cache specific quirks, like the long timeouts in Memcached, must be
handled in the subclass implementation.

In addition, one can specify the grace time per value. The grace time is the
number of seconds a client is given to try to produce a new value after the
current value has timed out. If the client fails to produce a new value within
the grace period, a new client is given the chance for an equally long time.
"""


__author__ = "Torgeir Lorange Østby"
__version__ = "1.1.3"
__docformat__ = "restructuredtext"


import time


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
        Set the wrapper values.
        """

        self.value = value
        self.soft_timeout = soft_timeout # Absolute
        self.hard_timeout = hard_timeout # Relative
        self.grace_time = grace_time # Relative


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
                hours.
        :param default_grace_time: The default is 60 seconds.
        """

        self.hard_timeout_factor = int(kwargs.pop("hard_timeout_factor", 8))
        self.default_grace_time = int(kwargs.pop("default_grace_time", 60))

    def _set_directly(self, key, value, timeout, **kwargs):
        """
        Some of the methods below need to be able to put values in the cache
        directly. A subclass must implement this method in order to allow that.
        """

        raise NotImplementedError()

    def _add_anti_dogpiling(self, value, timeout, grace_time=None):
        """
        Add a wrapper around the value with data needed later by the
        anti-dogpiling mechanisms. A new value and timeout is returned.
        """

        soft_timeout = timeout + _now()
        hard_timeout = timeout * self.hard_timeout_factor
        grace_time = grace_time or self.default_grace_time

        wrapped_value = Wrapper(value, soft_timeout, hard_timeout, grace_time)

        return wrapped_value, hard_timeout

    def _is_anti_dogpiled(self, value):
        """
        Check if the given value is wrapped in an anti-dogpiling wrapper. Use
        this when fetching values from the cache.
        """

        return isinstance(value, Wrapper)

    def _apply_anti_dogpiling(self, key, value, **kwargs):
        """
        Apply the anti-dogpiling mechanisms to the provided key and value. Use
        this when fetching values from the cache.
        """

        now = _now()

        # If no timeout, just return the value
        if value.soft_timeout >= now:
            return value.value

        # We have a soft timeout. The client gets the grace period to produce
        # and set an updated value while everyone else gets the old value.
        value.soft_timeout = now + value.grace_time
        self._set_directly(key, value, value.hard_timeout, **kwargs)

        return None

    def _soft_invalidate(self, key, value, **kwargs):
        """
        Invalidate an anti-dogpiled value while keeping the properties of
        anti-dogpiling.
        """

        value.soft_timeout = 0
        self._set_directly(key, value, value.hard_timeout, **kwargs)
