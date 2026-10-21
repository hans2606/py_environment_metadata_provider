"""Tests for py_environment_metadata_provider.core."""

import os
import platform
import unittest
from types import MappingProxyType

from py_environment_metadata_provider.core import (
    EnvironmentMetadataProvider,
    EnvironmentMetadata,
)


class TestEnvironmentMetadataProvider(unittest.TestCase):
    def setUp(self):
        self.fake_clock_value = 1_700_000_000.0
        self.fake_clock = lambda: self.fake_clock_value
        self.provider = EnvironmentMetadataProvider(clock=self.fake_clock)

    # ------------------------------------------------------------------
    # Happy path: all expected keys are present with correct types
    # ------------------------------------------------------------------
    def test_has_all_expected_keys(self):
        md = self.provider.metadata
        self.assertEqual(
            set(md.keys()),
            {"hostname", "pid", "python_version", "boot_time"},
        )

    def test_hostname_is_string(self):
        self.assertIsInstance(self.provider.metadata["hostname"], str)

    def test_pid_is_int_and_matches_os(self):
        self.assertEqual(self.provider.metadata["pid"], os.getpid())
        self.assertIsInstance(self.provider.metadata["pid"], int)

    def test_python_version_matches_platform(self):
        self.assertEqual(
            self.provider.metadata["python_version"],
            platform.python_version(),
        )

    def test_boot_time_uses_injected_clock(self):
        self.assertEqual(self.provider.metadata["boot_time"], 1_700_000_000.0)

    # ------------------------------------------------------------------
    # Immutability guarantee
    # ------------------------------------------------------------------
    def test_metadata_is_mapping_proxy(self):
        self.assertIsInstance(self.provider.metadata, MappingProxyType)

    def test_metadata_is_frozen(self):
        md = self.provider.metadata
        with self.assertRaises(TypeError):
            md["hostname"] = "tampered"  # type: ignore[index]
        with self.assertRaises(TypeError):
            del md["pid"]  # type: ignore[misc]

    # ------------------------------------------------------------------
    # as_dict returns an independent mutable copy
    # ------------------------------------------------------------------
    def test_as_dict_returns_plain_dict(self):
        d = self.provider.as_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d, dict(self.provider.metadata))

    def test_as_dict_is_mutable_and_independent(self):
        d = self.provider.as_dict()
        d["hostname"] = "changed"
        d["extra"] = 42
        # Original metadata must be unaffected
        self.assertNotEqual(self.provider.metadata["hostname"], "changed")
        with self.assertRaises(KeyError):
            self.provider.metadata["extra"]  # type: ignore[index]

    # ------------------------------------------------------------------
    # Boot time is captured exactly once at construction
    # ------------------------------------------------------------------
    def test_boot_time_captured_once(self):
        # Change what the fake clock would return AFTER construction.
        self.fake_clock_value = 1_800_000_000.0
        self.assertEqual(self.provider.metadata["boot_time"], 1_700_000_000.0)

    def test_multiple_providers_get_independent_boot_times(self):
        first = EnvironmentMetadataProvider(clock=lambda: 100.0)
        second = EnvironmentMetadataProvider(clock=lambda: 200.0)
        self.assertEqual(first.metadata["boot_time"], 100.0)
        self.assertEqual(second.metadata["boot_time"], 200.0)

    # ------------------------------------------------------------------
    # EnvironmentMetadata type alias is importable
    # ------------------------------------------------------------------
    def test_environment_metadata_type_is_importable(self):
        self.assertTrue(hasattr(EnvironmentMetadata, "__class__"))


if __name__ == "__main__":
    unittest.main()
