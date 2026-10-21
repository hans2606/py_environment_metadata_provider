"""Collect static environment metadata for log record enrichment.

This module gathers four pieces of information once at startup:
hostname, process id, Python version, and boot time. After collection
the data is exposed as a frozen (immutable) mapping so that it can be
shared safely across threads without risk of mutation, and merged into
log records consistently for the lifetime of the process.
"""

from __future__ import annotations

import os
import platform
import socket
import sys
import time
from types import MappingProxyType
from typing import Mapping


# Public type alias so users can annotate against the frozen dict shape
# without importing the private implementation details.
EnvironmentMetadata = Mapping[str, object]


class EnvironmentMetadataProvider:
    """Collect environment metadata once and expose it as a frozen dict.

    Parameters
    ----------
    clock:
        A callable returning the current time as a float, in the same
        units as :func:`time.time` (seconds since the Unix epoch). The
        default is :func:`time.time`. Accepting a clock function keeps
        construction deterministic for tests; without it, a test that
        checks the recorded boot time would have to compare against
        :func:`time.time` in a separate call and race the scheduler.

    Notes
    -----
    ``socket.gethostname`` can raise ``OSError`` on systems where the
    hostname is not configured. We fall back to the string ``"<unknown>"``
    rather than letting provider construction crash the host application;
    a missing hostname in a log line is annoying, but failing to construct
    the logging provider is worse.

    ``platform.python_version`` is used instead of :data:`sys.version`
    because the latter is a multi-line human-readable string unsuitable
    for structured logging. ``platform.python_version`` returns a compact
    ``"major.minor.patch"`` string that sorts correctly and is easy to
    filter on.
    """

    __slots__ = ("_metadata",)

    def __init__(self, clock=time.time) -> None:
        try:
            hostname = socket.gethostname()
        except OSError:
            # No configured hostname — record a sentinel rather than
            # propagating the failure, so logging can still be set up.
            hostname = "<unknown>"

        boot_time = clock()

        self._metadata: EnvironmentMetadata = MappingProxyType(
            {
                "hostname": hostname,
                "pid": os.getpid(),
                "python_version": platform.python_version(),
                "boot_time": boot_time,
            }
        )

    @property
    def metadata(self) -> EnvironmentMetadata:
        """Return the collected environment metadata as a frozen dict.

        The returned :class:`types.MappingProxyType` is read-only; any
        attempt to mutate it raises :class:`TypeError`. This guarantee
        lets the same provider instance be shared across threads.
        """
        return self._metadata

    def as_dict(self) -> dict:
        """Return a plain mutable copy of the metadata.

        Useful when the consumer needs to merge additional fields into
        the record and does not want a :class:`MappingProxyType` in the
        chain (some serializers handle proxies poorly).
        """
        return dict(self._metadata)
