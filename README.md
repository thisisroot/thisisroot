<div align="center">

<sub>INDEPENDENT BUILDER · SYSTEMS / PRODUCT</sub>

# `thisisroot`

I build software where the protocol, product, and infrastructure are designed as one system.

<br />

**Currently:** Trust — a cross-platform messenger built to be self-hosted.

</div>

---

### `trust/`

One product, split along real boundaries: a Flutter client, a Rust reference server, a versioned wire contract, and a shared cryptography core.

| Surface | What I'm working on |
| --- | --- |
| [Client](https://github.com/thisisroot/trust-client) | One app across mobile, desktop, and web; motion-led, monochrome interface. |
| [Protocol](https://github.com/thisisroot/trust-protocol) | Versioned REST + WebSocket contracts, with schemas as the source of truth. |
| [Server](https://github.com/thisisroot/trust-server) | Rust backend for accounts, messaging, realtime delivery, and media. |
| [Crypto](https://github.com/thisisroot/trust-crypto) | Shared Rust MLS core, intended to give every client one cryptographic implementation. |
| [Deployment](https://github.com/thisisroot/trust-deploy) | Self-hosting pieces for running the service on your own infrastructure. |

<br />

```text
DESIGN BIAS
  small, explicit contracts
  replaceable implementations
  self-hosting as a first-class path
  polish in the details, not decoration
```

The encryption boundary is a core design goal; the MLS work is still being integrated into the app.

<div align="right"><sub>LESS MAGIC. MORE OWNERSHIP.</sub></div>
