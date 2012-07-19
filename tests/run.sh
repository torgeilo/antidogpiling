#!/bin/sh

set -e

test ! -f bin/nosetests \
    && python bootstrap.py --distribute \
    && bin/buildout

bin/nosetests --with-coverage --cover-package=antidogpiling
