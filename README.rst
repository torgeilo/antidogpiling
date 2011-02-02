=============
antidogpiling
=============

The antidogpiling framework is a generic set of functionality for implementing anti-dogpiled caching. It currently includes completed implementations for all the Django 1.2 cache backends.

Dogpiling is the effect you get when a cached value times out, and everyone rushes to create a new value. The anti-dogpiling tries to mitigate this by serving the old value while waiting for a few (ideally one) who are let through to produce a new value.

Benefits of using this package compared to others:

- It provides the generic functionality
- It wraps the cached data in a custom object and not in a tuple or dict or so, making it possible to actually cache tuples or dicts which would potentially conflict with the internal handling
- It supports all Django 1.2 cache backends, without re-implementing any Django functionality

Using the anti-dogpiled Django 1.2 backends
===========================================

Simply set the ``CACHE_BACKEND`` setting to point to the right module. A few examples::

  CACHE_BACKEND = "antidogpiling.django.memcached://127.0.0.1:11211/"
  CACHE_BACKEND = "antidogpiling.django.filebased:///var/tmp/django_cache"
