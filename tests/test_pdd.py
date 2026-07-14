import json

from product_reco_bot.integrations.pdd import PddClient, PddCredentials


def test_pdd_signature_is_stable() -> None:
    client = PddClient(PddCredentials("client", "secret", "pid"))

    signature = client._sign({"type": "example", "timestamp": 123, "client_id": "client"})

    assert signature == "001CE0AF2B3B880CE83AA0E4AC0CB857"


def test_pdd_error_redaction() -> None:
    client = PddClient(PddCredentials("client-id", "super-secret", "pid-value"))

    message = client._redact("client-id super-secret pid-value")

    assert message == "*** *** ***"


def test_pdd_transport_retries_once(monkeypatch) -> None:
    calls = 0

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"goods_search_response": {"goods_list": []}}).encode()

    def fake_urlopen(request, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError
        return Response()

    monkeypatch.setattr("product_reco_bot.integrations.pdd.urlopen", fake_urlopen)
    monkeypatch.setattr("product_reco_bot.integrations.pdd.time.sleep", lambda seconds: None)
    client = PddClient(PddCredentials("client", "secret", "pid"), max_attempts=2)

    result = client.search_goods("玩具")

    assert calls == 2
    assert result["goods_search_response"]["goods_list"] == []
