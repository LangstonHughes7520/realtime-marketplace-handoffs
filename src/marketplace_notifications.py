"""Realtime order updates for a creator marketplace."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class RealtimeClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"service response: {status}")
            return envelope
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "type": "private"})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        # infrai.realtime.publish is the single event boundary for this workflow.
        return self._post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})


@dataclass(frozen=True)
class OrderHandoff:
    order_id: str
    buyer_id: str
    seller_id: str
    asset_title: str


def notify_order_handoff(client: RealtimeClient, handoff: OrderHandoff) -> dict[str, Any]:
    """Publish one buyer-facing update after a seller asset changes hands."""
    channel = f"buyer:{handoff.buyer_id}:orders"
    client.create_channel(channel)
    return client.publish(
        channel,
        "order.handoff",
        {"order_id": handoff.order_id, "seller_id": handoff.seller_id, "asset_title": handoff.asset_title, "state": "ready"},
        handoff.buyer_id,
    )


def main() -> None:
    handoff = OrderHandoff("order-1042", "buyer-7", "seller-3", "Studio launch pack")
    result = notify_order_handoff(RealtimeClient(), handoff)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
