# py_environment_metadata_provider

Collects hostname, process ID, Python version, and boot time once at startup, exposing them as a frozen dict for log record enrichment.

## Usage

```python
from py_environment_metadata_provider import EnvironmentMetadataProvider

provider = EnvironmentMetadataProvider()
metadata = provider.metadata          # MappingProxyType — read-only
# metadata == {
#     "hostname": "web-01",
#     "pid": 42137,
#     "python_version": "3.12.1",
#     "boot_time": 1735689600.0,
# }

mutable = provider.as_dict()          # plain dict copy, safe to extend
mutable["service"] = "billing"
```

`EnvironmentMetadataProvider(clock=...)` accepts a clock callable (default `time.time`) so construction is deterministic in tests.

## Why

Structured log records are only useful if every line carries enough context to be filtered without ambiguity. Hostname, PID, Python version, and process start time together answer "which machine, which process, which runtime, how long has it been up" in a single merge. Collecting these values once at startup — rather than per-log-call — avoids redundant system calls and guarantees every record sees identical values, which makes downstream deduplication reliable.

The trade-off is freshness: if a process changes its hostname at runtime (rare), the metadata will not reflect that. This is acceptable for logging because the value of consistency outweighs the value of a hostname update that arrives mid-stream.

## Edge cases

`socket.gethostname` can raise `OSError` on misconfigured systems. Rather than propagating the failure and crashing the host application, the provider records the sentinel string `"<unknown>"` for `hostname`. Log consumers should handle that sentinel gracefully.

The frozen mapping returned by `.metadata` is a `types.MappingProxyType`. Some serializers (notably older JSON encoders) do not traverse proxy objects transparently; use `.as_dict()` when you need a plain `dict`.
