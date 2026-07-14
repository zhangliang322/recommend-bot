from product_reco_bot.integrations.pdd import PddClient, PddCredentials


def test_pdd_signature_is_stable() -> None:
    client = PddClient(PddCredentials("client", "secret", "pid"))

    signature = client._sign({"type": "example", "timestamp": 123, "client_id": "client"})

    assert signature == "001CE0AF2B3B880CE83AA0E4AC0CB857"


def test_pdd_error_redaction() -> None:
    client = PddClient(PddCredentials("client-id", "super-secret", "pid-value"))

    message = client._redact("client-id super-secret pid-value")

    assert message == "*** *** ***"
