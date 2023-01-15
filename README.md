# kcp.py
Python bindings and abstractions for the KCP protocol.

## What is KCP?
KCP is a protocol focusing on low latency data delivery with a guarantee of data delivery. It serves as an alternative to the TCP protocol.

## Features
- [x] Bindings to the C implementation of KCP
- [x] Pythonic API over said C bindings
- [ ] Asynchronous KCP Client
- [x] Synchronous KCP Client
- [ ] Asynchronous KCP Server
- [ ] Full support for installation through pip

## Credit
kcp.py uses [the official KCP implementation](https://github.com/skywind3000/kcp) behind the scenes.
