from setuptools import setup, find_packages

import antidogpiling


setup(
    name="antidogpiling",
    version=antidogpiling.__version__,
    author=antidogpiling.__author__,
    author_email="torgeilo@gmail.com",
    url="http://github.com/torgeilo/antidogpiling",
    description="Generic and specific implementations of anti-dogpiled caching",
    long_description=open("README.rst").read(),
    classifiers=(
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ),
    keywords="caching anti-dogpiling",
    license="BSD",
    packages=find_packages(exclude=["tests"]),
    zip_safe=True,
)
