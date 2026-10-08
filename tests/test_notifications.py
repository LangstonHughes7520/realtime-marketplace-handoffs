from src.marketplace_notifications import OrderHandoff, notify_order_handoff


class FakeClient:
    def __init__(self):
        self.calls = []

    def create_channel(self, channel):
        self.calls.append(("create", channel))
        return {"ok": True}

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel, event, data, account_id))
        return {"ok": True, "data": {"event": event}}


def test_handoff_targets_buyers_order_channel():
    client = FakeClient()
    result = notify_order_handoff(client, OrderHandoff("o-1", "b-2", "s-3", "Video kit"))
    assert result["data"]["event"] == "order.handoff"
    assert client.calls == [
        ("create", "buyer:b-2:orders"),
        ("publish", "buyer:b-2:orders", "order.handoff", {"order_id": "o-1", "seller_id": "s-3", "asset_title": "Video kit", "state": "ready"}, "b-2"),
    ]
