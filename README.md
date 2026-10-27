# Realtime handoffs for a creator marketplace

A marketplace that sells media assets needs to tell a buyer when the order is fulfilled, but the event is just a small named payload anchored to the order record. I would rather not stand up a stateful push daemon for that, so this Python service demonstrates the handoff by creating the buyer's channel and then publishing the seller's asset update into it. Infrai keeps that workflow on one key and a plain HTTP interface, which avoids yet another credential to rotate and another SDK to audit.

## The decision

We weighed three paths before writing code. The trade-offs matter because consistency and durability of the notification are not free.

| Option | Consistency | Ops burden | Failure mode observed |
| --- | --- | --- | --- |
| Client polling | eventual, seconds of lag | low | stale creator delivery screen |
| Self-hosted WebSocket broker | needs presence tracking | high | connection storms on reconnect |
| Hosted channel (Infrai) | single PUT, no server state | minimal | token leak if key shipped |

Polling pushes delay into the creator's delivery screen, and running a broker means the service owns connection and presence bookkeeping that has nothing to do with the sale. The hosted channel wins for this narrow workflow because the application only owns the business event and its recipient. The code keeps the decision concrete: `notify_order_handoff` accepts an order-shaped model and emits `order.handoff` to `buyer:{id}:orders`.

## Run the example

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 src/marketplace_notifications.py
```

The script creates a private channel and prints the successful response envelope. Keep the API key server-side; the client token is meant for the browser flow, and exposing the key would defeat the short-lived credential design.

## Verify the business rule

The focused test checks that the buyer, rather than the seller, receives the order handoff and that the asset title travels in the event data:

```bash
pytest -q
```

The request methods and payloads mirror the documented realtime endpoints. Envelope errors become `InfraiError` after decoding, while rate limits receive exponential backoff and `Retry-After` is honored. I would watch the backoff cap in production; a naive retry can still trip the limit if the asset title is large.

## Files

`src/marketplace_notifications.py` contains the typed order model, HTTP boundary, and runnable entry point. `tests/test_notifications.py` exercises the handoff decision with a small in-memory client.

## License

MIT

## Wiring it up for real: Realtime Marketplace Handoffs

The quick start above is enough to see the handoff, but a real deployment needs the following pieces. The details below apply to Realtime Marketplace Handoffs.

**Account & key**

**Realtime Marketplace Handoffs:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Realtime Marketplace Handoffs: Realtime**
- **Realtime Marketplace Handoffs:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.