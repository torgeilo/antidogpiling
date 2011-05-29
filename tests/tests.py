import time

from mock import Mock
from unittest import TestCase

from antidogpiling import Wrapper
from antidogpiling.django.common import Cache


class MockBackendMixin(object):
    """
    Mocks a cache backend which is to be mixed with the Cache class.
    """

    def __init__(self, *args, **kwargs):
        self._cache = Mock()

    def add(self, key, value, timeout=None, version=None):
        self._cache.add(key, value, timeout, version=version)

    def set(self, key, value, timeout=None, version=None):
        self._cache.set(key, value, timeout, version=version)

    def get(self, key, default=None, version=None):
        val = self._cache.get(key, version=version)
        if val is not None:
            return val
        return default

    def delete(self, key, version=None):
        self._cache.delete(key, version=version)


class CacheMixinTestCase(TestCase):
    """
    Tests for the Cache and AntiDogpiling classes.
    """

    def setUp(self):
        self.cache = Cache(MockBackendMixin, None, {})
        self.mock = self.cache._cache

    def test_add_soft(self):
        """
        Test adding a value to the cache with anti-dogpiling. The cached value
        should be wrapped in a anti-dogpiling object with timeouts.
        """

        now = int(time.time())
        self.cache.add("foo", "bar", timeout=1)

        # Check that the add method was called once
        self.assertEquals(1, self.mock.add.call_count)

        # Check the arguments to the add method
        args = self.mock.add.call_args
        self.assertEquals("foo", args[0][0])
        self.assertEquals(Wrapper, type(args[0][1]))
        self.assertEquals(8, args[0][2])
        self.assertEquals("bar", args[0][1].value)
        self.assertEquals(8, args[0][1].hard_timeout)
        self.assertEquals(60, args[0][1].grace_time)
        self.assertEquals(1, args[0][1].soft_timeout - now)

    def test_add_hard(self):
        """
        Test adding a value to the cache without anti-dogpiling. The cached
        value should be added to the cache as is.
        """

        self.cache.add("foo", "bar", timeout=1, hard=True)
        self.mock.add.assert_called_with("foo", "bar", 1, version=None)

    def test_add_hard_with_version(self):
        """
        Test adding a value to the cache without anti-dogpiling. The cached
        value should be added to the cache as is. It is basically the same test
        as above, just with a version argument.
        """

        self.cache.add("foo", "bar", timeout=1, hard=True, version=2)
        self.mock.add.assert_called_with("foo", "bar", 1, version=2)

    def test_set_soft(self):
        """
        Test setting a value in the cache with anti-dogpiling. The cached value
        should be wrapped in a anti-dogpiling object with timeouts.
        """

        now = int(time.time())
        self.cache.set("foo", "bar", timeout=2)

        # Check that the add method was called once
        self.assertEquals(1, self.mock.set.call_count)

        # Check the arguments to the add method
        args = self.mock.set.call_args
        self.assertEquals("foo", args[0][0])
        self.assertEquals(Wrapper, type(args[0][1]))
        self.assertEquals(16, args[0][2])
        self.assertEquals("bar", args[0][1].value)
        self.assertEquals(16, args[0][1].hard_timeout)
        self.assertEquals(60, args[0][1].grace_time)
        self.assertEquals(2, args[0][1].soft_timeout - now)

    def test_set_hard(self):
        """
        Test setting a value in the cache without anti-dogpiling. The cached
        value should be set as is.
        """

        self.cache.set("foo", "bar", timeout=1, hard=True)
        self.mock.set.assert_called_with("foo", "bar", 1, version=None)

    def test_set_hard_with_version(self):
        """
        Test setting a value in the cache without anti-dogpiling. The cached
        value should be set as is. It is basically the same test as above, just
        with a version argument.
        """

        self.cache.set("foo", "bar", timeout=1, hard=True, version=3)
        self.mock.set.assert_called_with("foo", "bar", 1, version=3)

    def test_get_soft_cache_hit(self):
        """
        Test getting an anti-dogpiled value from the cache which has not timed
        out in any way. The cached value should just be returned without
        further ado.
        """

        now = int(time.time())
        self.mock.get = Mock(return_value=Wrapper("bar", now + 100, 1000, 60))

        value = self.cache.get("foo")
        self.assertEquals("bar", value)

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=None)

        # Check that the set method was not called
        self.assertFalse(self.mock.set.called)

    def test_get_soft_cache_miss(self):
        """
        Test getting an anti-dogpiled value from the cache which has timed out
        softly. The cached value should not be returned, the default value
        should, but the cache should be updated with a new soft timeout (so
        that all following requests get the cached value while it is being
        updated by the current request).
        """

        now = int(time.time())
        self.mock.get = Mock(return_value=Wrapper("bar", now - 10, 1000, 60))

        value = self.cache.get("foo", default="default")
        self.assertEquals("default", value)

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=None)

        # Check the set method and arguments
        self.assertEquals(1, self.mock.set.call_count)
        args = self.mock.set.call_args
        self.assertEquals("foo", args[0][0])
        self.assertEquals(Wrapper, type(args[0][1]))
        self.assertEquals(1000, args[0][2])
        self.assertEquals("bar", args[0][1].value)
        self.assertEquals(1000, args[0][1].hard_timeout)
        self.assertEquals(60, args[0][1].grace_time)
        self.assertEquals(60, args[0][1].soft_timeout - now)

    def test_get_hard_cache_hit(self):
        """
        Test getting a non-anti-dogpiled value from the cache which has not
        timed out. The cached value should just be returned without any futher
        ado.
        """

        self.mock.get = Mock(return_value="bar")

        value = self.cache.get("foo")
        self.assertEquals("bar", value)

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=None)

        # Check that the set method was not called
        self.assertFalse(self.mock.set.called)

    def test_get_hard_cache_hit_with_version(self):
        """
        Test getting a non-anti-dogpiled value from the cache which has not
        timed out. The cached value should just be returned without any futher
        ado. It is basically the same test as above, just with a version
        argument.
        """

        self.mock.get = Mock(return_value="bar")

        value = self.cache.get("foo", version=4)
        self.assertEquals("bar", value)

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=4)

        # Check that the set method was not called
        self.assertFalse(self.mock.set.called)

    def test_get_hard_cache_miss(self):
        """
        Test getting a non-anti-dogpiled value from the cache which has timed
        out (or, ). The cache should just return the default value.
        """

        self.mock.get = Mock(return_value=None)

        value = self.cache.get("foo", default="default")
        self.assertEquals("default", value)

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=None)

    def test_delete_soft_adp(self):
        """
        Test that soft-deleting an anti-dogpiled value just soft-invalidates
        it.
        """

        now = int(time.time())
        self.mock.get = Mock(return_value=Wrapper("bar", now, 1000, 120))

        self.cache.delete("foo")

        # Check the delete method
        self.assertFalse(self.mock.delete.called)

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=None)

        # Check the set method
        self.assertEquals(1, self.mock.set.call_count)
        args = self.mock.set.call_args
        self.assertEquals("foo", args[0][0])
        self.assertEquals(Wrapper, type(args[0][1]))
        self.assertEquals(1000, args[0][2])
        self.assertEquals("bar", args[0][1].value)
        self.assertEquals(1000, args[0][1].hard_timeout)
        self.assertEquals(120, args[0][1].grace_time)
        self.assertEquals(0, args[0][1].soft_timeout) # Soft timestamp 0

    def test_delete_hard_adp(self):
        """
        Test that hard-deleting an anti-dogpiled value actually deletes it.
        """

        now = int(time.time())
        self.mock.get = Mock(return_value=Wrapper("bar", now, 1000, 60))

        self.cache.delete("foo", hard=True)

        # Check the delete method
        self.assertEquals(1, self.mock.delete.call_count)
        self.mock.delete.assert_called_with("foo", version=None)

        # Check other methods
        self.assertFalse(self.mock.get.called)
        self.assertFalse(self.mock.set.called)

    def test_delete_hard_adp_with_version(self):
        """
        Test that hard-deleting an anti-dogpiled value actually deletes it. It
        is basically the same test as above, just with a version argument.
        """

        now = int(time.time())
        self.mock.get = Mock(return_value=Wrapper("bar", now, 1000, 60))

        self.cache.delete("foo", hard=True, version=5)

        # Check the delete method
        self.assertEquals(1, self.mock.delete.call_count)
        self.mock.delete.assert_called_with("foo", version=5)

        # Check other methods
        self.assertFalse(self.mock.get.called)
        self.assertFalse(self.mock.set.called)

    def test_delete_soft_nadp(self):
        """
        Test that soft-deleting a non-anti-dogpiled value actually deletes it.
        """

        self.mock.get = Mock(return_value="bar")

        self.cache.delete("foo")

        # Check the get method
        self.assertEquals(1, self.mock.get.call_count)
        self.mock.get.assert_called_with("foo", version=None)

        # Check the delete method
        self.assertEquals(1, self.mock.delete.call_count)
        self.mock.delete.assert_called_with("foo", version=None)

        # Check the set method
        self.assertFalse(self.mock.set.called)

    def test_delete_hard_nadp(self):
        """
        Test that hard-deleting a non-anti-dogpiled value actually deletes it.
        """

        self.mock.get = Mock(return_value="bar")

        self.cache.delete("foo", hard=True)

        # Check the delete method
        self.assertEquals(1, self.mock.delete.call_count)
        self.mock.delete.assert_called_with("foo", version=None)

        # Check other methods
        self.assertFalse(self.mock.get.called)
        self.assertFalse(self.mock.set.called)
