# DemonCore Protocol (DCP) v1

Status: v1.0 normative contract. Encoding is UTF-8 JSON; one complete message is one JSON object.

## Envelope
Every message has exactly: `v` (integer major version, currently 1), `id` (16–32 lowercase hex characters), `src` (concrete `node:<positive-id>`), `dst` (address selector), `t` (`req`, `res`, `evt`), `op` (namespaced operation), and `args` (object, including when empty). Unknown envelope fields are rejected in v1.

## Addressing
- `node:<decimal-id>`: one node, positive decimal ID.
- `group:<slug>`, `tag:<slug>`, `cell:<slug>`: configured selectors.
- `*`: every reachable node; destination only.
A slug is 1–32 lowercase ASCII letters, digits, underscore or hyphen, beginning with a letter. `src` must be a concrete node address. Unresolved selectors return `E_NOT_FOUND`.

## Types and correlation
- `req`: request; ID is unique among the sender's outstanding requests.
- `res`: response; copies request ID and op, with src/dst reversed.
- `evt`: unsolicited event; ID is a new event identifier.
Successful responses put operation response fields in args. Failed responses use `args: {"error":{"code":"E_*","message":"short description","details":{}}}`; details may be omitted. Requests/events must not carry error objects.

## Limits and fragmentation
Maximum encoded message size is 4,096 bytes after UTF-8 JSON encoding. Args nesting depth is at most 8 and each object/array has at most 64 members. Reject invalid UTF-8, duplicate JSON keys, NaN and infinities. Larger transport frames are fragmented by the transport adapter; DCP application fields do not carry fragment metadata. Reassembly is bounded to 4,096 bytes and one in-flight message per peer by default. Each adapter documents its frame size, timeout and fragment numbering. Oversize, malformed or incomplete messages are discarded without partial execution.

## Errors
`E_BAD_MESSAGE` malformed envelope/JSON; `E_VERSION` unsupported version; `E_NOT_FOUND` unresolved destination/resource; `E_UNSUPPORTED` unknown operation/capability; `E_INVALID_ARG` missing/extra/out-of-range argument; `E_DENIED` unauthorised; `E_PIN_BLOCKED` forbidden pin; `E_CONFIRM_REQUIRED` warned action needs confirmation; `E_BUSY` resource busy; `E_TIMEOUT` timed out; `E_TOO_LARGE` size/reassembly limit; `E_INTERNAL` unexpected failure. Error responses retain request id/op. Never include credentials or keys in errors.

## Initial operations
The argument and response contracts are in [ops.json](ops.json): `sys.info`, `sys.ping`, `gpio.mode`, `gpio.read`, `gpio.write`. GPIO schema-valid pins are not necessarily safe: every operation must also pass the data-driven board pin validator.

## Compatibility and security
v1 uses `v: 1`; changes to field meaning are forbidden. New fields require a documented minor-version extension before implementation. This envelope does not authenticate traffic. Authentication/encryption belong to the security tasks; do not improvise cryptography or put domain keys in vectors. Claimed nodes must reject unauthenticated traffic once that layer is implemented.
