#! /usr/bin/env python

# Imports

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime
import os
import semver
from string import Template
import sys
from ..shortcuts import write_file

# Administrivia

__author__ = "Shawn Davis <shawn@ptltd.co>"
__command__ = os.path.basename(sys.argv[0])
__date__ = "2016-11021"
__version__ = "0.9.2-d"

# Constants

NOW = datetime.now()

PROJECT_HOME = os.environ.get("PROJECT_HOME", "~/Work")

TEMPLATE = """# Generated by versionbump.py $now
major = $major
minor = $minor
patch = $patch
status = "$prerelease"
build = "$build"
name = "$name"


def get_release():
    r = "%s.%s.%s" % (major, minor, patch)

    if status:
        r += "-%s" % status

    return r


def get_version():
    return "%s.%s" % (major, minor)


RELEASE = get_release()
VERSION = get_version()

"""

# Classes


class Version(object):
    """Represents a version/release."""

    def __init__(self, string):
        self._current = None
        self._original = string
        self.object = semver.parse_version_info(string)

    def __str__(self):
        return self.to_string()

    @property
    def build(self):
        return self.object.build

    def bump(self, major=None, minor=None, patch=None, status=None, build=None):
        """Bump the version."""

        # Number positions are mutually exclusive.
        if major:
            self._current = semver.bump_major(self._original)
        elif minor:
            self._current = semver.bump_minor(self._original)
        elif patch:
            self._current = semver.bump_patch(self._original)
        else:
            self._current = self._original

        # Set the status.
        if status:
            self._current += "-%s" % status
        elif self.object.prerelease:
            self._current += "-%s" % self.object.prerelease
        else:
            pass

        # Set the build.
        if build:
            self._current += "+%s" % build
        elif self.object.build:
            self._current += "+%s" % self.object.build
        else:
            pass

        self.object = semver.parse_version_info(self._current)

    def get_context(self):
        """Get the version as a dictionary.

        :rtype: dict

        """
        tokens = semver.parse(self.to_string())

        tokens['name'] = ""
        tokens['now'] = NOW

        if tokens['build'] is None:
            tokens['build'] = ""

        if tokens['prerelease'] is None:
            tokens['prerelease'] = ""

        return tokens

    @staticmethod
    def get_template():
        """Get the template used for Python ``version.py`` files.

        :rtype: str

        """
        return TEMPLATE

    @property
    def major(self):
        return self.object.major

    @property
    def minor(self):
        return self.object.minor

    @property
    def patch(self):
        return self.object.patch

    @property
    def prerelease(self):
        return self.object.prerelease

    @property
    def status(self):
        """Alias of prerelease."""
        return self.object.prerelease

    def to_string(self):
        """Get the version string.

        :rtype: str

        """
        return self._current or self._original
