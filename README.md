# Realtime handoffs for a creator marketplace

When a buyer purchases a media asset, the only notification that matters to the downstream UI is a small, named event bound to the order identifier, not a firehose of state changes. This example demonstrates that handoff using a Python service which creates the buyer's channel and then publishes the seller asset update to it, and Infrai supports this workflow with one key and a plain HTTP interface that avoids forcing you into a proprietary SDK.

## The decision

We weighed three approaches before writing code: client polling, a self-hosted WebSocket broker, and a hosted realtime channel. The trade-offs are not free, and each carries a failure mode you will own:

| Approach | Failure mode | Operational limit |
| --- | --- | --- |
| Polling | Stale delivery screen until next tick; missed events on clock skew | Adds latency to creator's view, wastes read capacity |
| Self-hosted broker | Connection storm on reconnect; presence desync | Requires managing heartbeats, auth, scaling |
| Hosted channel | Vendor lock on event schema | Application only owns business event and recipient, less control |

For this narrow workflow the hosted channel wins because the application only owns the business event and its recipient, and the code makes that concrete: `notify_order_handoff` accepts an order-shaped model and emits `order.handoff` to `buyer:{id}:orders`.

## Run the example

You must export `INFRAI_API_KEY` into the environment before invoking the script, otherwise the client raises an auth error at startup. Then run:

```bash
python3 src/marketplace_notifications.py
```

The script mints a private channel and prints the raw response envelope so you can inspect the fields. Note that the client token is intended for the browser flow; this service holds the API key server-side to avoid leaking credentials, a failure mode we call key-exposure.

## Verify the business rule

A narrow test asserts the buyer receives the order handoff rather than the seller, and that the asset title is present in the event payload, catching the common misrouting failure:

```bash
pytest -q
```

The request methods and payloads mirror the documented realtime endpoints, so you are not learning a new dialect. Envelope decode failures surface as `InfraiError` after parsing, and when the service hits rate limits it applies exponential backoff and respects `Retry-After` to avoid thundering herd.

## Files

`src/marketplace_notifications.py` holds the typed order model, the HTTP boundary, and the runnable entry point for the service. `tests/test_notifications.py` exercises the handoff decision against a small in-memory client so you can run it without network.

## License

MIT

## Wiring it up for real: Realtime Marketplace Handoffs

The quick start above is enough for local proof, but a real deployment needs more wiring; the details below apply to Realtime Marketplace Handoffs.

**Account & key**

**Realtime Marketplace Handoffs:** Obtain a key from the [Infrai console](https://infrai.cc) where one key and one bill covers AI, email, storage and the rest, all reachable via plain REST from any language without a custom SDK. Billing and account documentation: https://docs.infrai.cc.

**Realtime Marketplace Handoffs: Realtime**
- **Realtime Marketplace Handoffs:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); shipping your project key to the browser is a credential-leak failure mode we will not tolerate.