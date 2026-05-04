# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`kcp.py` is a Python library exposing the [KCP protocol](https://github.com/skywind3000/kcp) (a reliable-UDP, low-latency alternative to TCP) through Cython bindings to the upstream C implementation, plus higher-level synchronous client and asyncio server abstractions. Distributed on PyPI as `kcp`.

## Commands

Build / dev install (Poetry drives the build, which invokes `build.py` to cythonize `kcp/extension.pyx` against `kcp/ikcp.c` and copy the compiled `.so`/`.pyd` back into the `kcp/` package so it's importable in-tree):

```sh
poetry install --with test          # install + compile the extension
poetry build                        # build wheel/sdist (also via `make build`)
```

Tests:

```sh
poetry run pytest                                    # all tests
poetry run pytest tests/bindings_test.py::test_delivery   # single test
```

Disable C extension build (rare — yields a non-functional package, but useful if Cython/toolchain is unavailable for static analysis):

```sh
KCP_PY_EXTENSIONS=0 poetry install
```

Formatting is enforced via pre-commit (`black` line length 100, `isort` with black profile, `pyupgrade --py37-plus`, `reorder-python-imports` which auto-injects `from __future__ import annotations`). Run `pre-commit run --all-files` before pushing.

CI (`.github/workflows/test.yml`) runs pytest on Python 3.11; release workflow builds wheels for Python 3.8–3.13 across Linux/Windows/macOS.

## Architecture

Three layers, bottom-up:

1. **`kcp/ikcp.c` + `kcp/ikcp.h`** — vendored upstream KCP C implementation from skywind3000/kcp. **Do not modify**; treat as a third-party dependency. Bug fixes belong upstream.

2. **`kcp/extension.pyx`** — Cython binding compiled to `kcp.extension`. Exposes a single class `KCP` that wraps `IKCPCB` (the C control block). The pyi sibling (`kcp/extension.pyi`) is the public type stub. Key design points:
   - `KCP` is connection-agnostic: it has no socket of its own. Outbound bytes leave via a user-registered callback (`include_outbound_handler` / `@outbound_handler` decorator). Inbound bytes are pushed in via `receive(data)`. Application-level reads come from `get_received()` / `get_all_received()`.
   - `update(ts_ms)` must be called periodically (~10–100ms) to drive retransmits, ACKs, and flushes — this is what triggers the outbound handler. `update_check()` returns the ms until the next required update.
   - Cython is configured with `boundscheck=False`, `wraparound=False`, `cdivision=True` — be cautious adding Python-level indexing in hot paths.

3. **`kcp/server.py` and `kcp/client.py`** — pure-Python networking layers that plug a UDP transport into a `KCP` instance via the outbound-handler hook:
   - `KCPServerAsync` (asyncio `DatagramProtocol`): one `Connection` per remote address, each owning its own `KCP`. `listen()` runs the update loop in-line with `asyncio.sleep(delay)`; idle connections past `connection_timeout` are GC'd. Note `datagram_received` schedules `connection.receive(data)` as a task — `_data_handler` is awaited per-packet.
   - `KCPClientSync`: blocking client driven by threads — receive thread reads from the UDP socket, main thread runs the KCP update loop. `_wait_for_address` blocks the receive loop until the first send so the OS-assigned local port is bound.
   - Both expose decorator-style hooks (`@on_data`, `@on_start`, `@on_stop`).

The single integration contract across all three layers is the **outbound-handler callback** — anything that wants to be a transport for KCP just needs to register one and call `kcp.receive(...)` when bytes arrive.

## Conventions

- Both ends of a KCP connection must share the same `conv_id`. This is the application-level demux key, not negotiated by the protocol.
- Public Python modules use `from __future__ import annotations` (enforced by pre-commit).
- The package ships pre-compiled binaries via the `*.so` / `*.pyd` includes in `pyproject.toml`; editing the `.pyx` requires rebuilding (`poetry install` or `poetry build`) for changes to take effect — Python imports the compiled extension, not the source.
