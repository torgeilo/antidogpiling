=============
antidogpiling
=============

This package provides a generic implementation and Django specific cache backends for anti-dogpiled caching. Django 1.2 and later are supported.

Dogpiling is the effect of everyone rushing to renew a value that has timed out in a cache, for as long as a new value has not yet been set. Anti-dogpiling tries do mitigate this by limiting how many gets to produce a new value. How the limiting is done, and what happens to everyone else, depends on the solution.

The solution provided in this package serves the old value from the cache while a new one is being produced. This is achieved by introducing a soft timeout for when the value should be renewed, in addition to the regular hard timeout (for when the value is no longer in the cache). At the event of a soft timeout, the first request is responded with a cache miss, and will go on to produce a new value, while subsequent requests are responded with the value that is still cached. When a new value is ready, it simply replaces the old value, and a new soft timeout is set.

In this particular implementation, as few requests as possible are let through to produce the new value, without using any locks (I have not tested using locks. Locking across servers could be tricky and undesirable. Unless letting only *one* call through to renew a value is a hard requirement, locking might not be worth the trouble).

See the `Benefits and caveats`_ section for important details.

Using the anti-dogpiled Django backends
=======================================

The anti-dogpiled Django backends are configured like Django's own backends. See the `Setting up the cache <https://docs.djangoproject.com/en/dev/topics/cache/#setting-up-the-cache>`_ in the Django documentation for details.

Django 1.2
----------

Simply set the ``CACHE_BACKEND`` setting to point to the right module. Examples::

  CACHE_BACKEND = 'antidogpiling.django.memcached://127.0.0.1:11211/'
  CACHE_BACKEND = 'antidogpiling.django.filebased:///var/tmp/django_cache'

Django 1.3+
-----------

Simply replace the ``BACKEND`` reference with the corresponding anti-dogpiled backend. An example::

  CACHES = {
      'default': {
          'BACKEND': 'antidogpiling.django.memcached.MemcachedCache',
          'LOCATION': '127.0.0.1:11211'.
      },
  }

Configuration options
---------------------

See the `cache options setting <https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CACHES-OPTIONS>`_ in the Django documentation on how to specify caching options.

Use the ``hard_timeout_factor`` option to control how much longer the hard timeout should be, relative to the soft timeout. The default is 8, so by default, the hard timeout is 8 times longer than the soft timeout. (The point is not to be able to specify an exact hard timeout, but to ensure that values stay in the cache for a sufficient amount of time for the anti-dogpiling to have an effect, and for unused values to eventually disappear from the cache.)

Use the ``default_grace_time`` option to set the timeout (in seconds) for *renewing* a value that has timed out softly. After this period, another client will be allowed to try producing a new value. The default is 60 seconds. The grace time can also be specified per call by using the ``grace_time`` parameter on the ``add`` and ``set`` methods.

An example for Django 1.3+::

  CACHES = {
      'default': {
          'BACKEND': 'antidogpiling.django.memcached.MemcachedCache',
          'LOCATION': '127.0.0.1:11211'.
          'OPTIONS': {
              'hard_timeout_factor': 100,
              'default_grace_time': 10,
          },
      },
  }

Client usage
------------

The ``add``, ``get``, ``set``, and ``delete`` methods work as usual, except that the timeouts set or invalidated are the soft timeouts, instead of the hard timeouts. To affect the hard timeouts, and to not apply any anti-dogpiling, use the ``hard=True`` parameter on the ``add``, ``set``, and ``delete`` methods.

**Note:** You must use ``hard=True`` when setting an integer to be used with the ``incr`` and ``decr`` methods. Increments and decrements require the raw integer to be stored in the cache.

See the caveats below for more details.

Benefits and caveats
====================

Benefits of using this package
------------------------------

- It provides the generic functionality, for anyone to base their own solution on.
- It wraps the cached data in a custom object---not in a tuple or dict or so---making it possible to cache tuples and dicts without conflicting with the internal workings of the anti-dogpiling.
- It supports all Django 1.2+ cache backends, without re-implementing any Django functionality.

General caveats
---------------

- There is no protection against dogpiling when a value is *not* in the cache *at all*.

Caveats in the Django backends
------------------------------

- The ``incr`` and ``decr`` are not anti-dogpiled due to being atomic in Memcached (at least). The anti-dogpiling would not be atomic, unless somehow implemented with locks. **Note:** When initializing a value for being incremented or decremented, one *has* to specify ``hard=True`` when calling the ``set`` method. Otherwise, the anti-dogpiling kicks in and stores a complex value which cannot be incremented (a ``ValueError`` is raised)!
- The ``set_many``, ``get_many``, and ``delete_many`` methods are not anti-dogpiled, due to a combination of laziness and all the decisions that would have to be made about how to handle soft timeouts, etc.

Change history
==============

1.1.3 (2012-07-19)
------------------

* Replaced the dynamic mixin with a regular object reference in the common
  Django backend, voiding the issue with using multiple different anti-dogpiled
  backends at the same time.
* Added dummy Django backend.

1.1.2 (2012-07-02)
------------------

* Documentation update (no functional change)

1.1.1 (2011-05-29)
------------------

* Added support for Django 1.3 backends

1.0.1 (2011-02-02)
------------------

* Added manifest file for proper packaging

1.0 (2011-02-02)
----------------

* Initial version
