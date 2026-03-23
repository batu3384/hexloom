from app.engine import TransformationEngine


engine = TransformationEngine()


def test_roundtrip_supported_methods():
    roundtrip_cases = [
        ("base64", "CipherDeck"),
        ("base64_double", "çözüm"),
        ("bytearray", "print('merhaba')"),
        ("html_entities", "<script>alert('x')</script>"),
        ("math_expr", "Merhaba"),
        ("rot13", "CipherDeck"),
        ("url_encode", "https://example.com/a b?x=1&y=2"),
        ("json_payload", 'console.log("x")'),
        ("morse", "SOS 2026"),
        ("hex", "Merhaba dünya"),
        ("binary", "Binary ✓"),
    ]

    for method, source in roundtrip_cases:
        encoded = engine.encode(source, method)
        assert encoded.status == "success", method
        assert encoded.result is not None, method

        decoded = engine.decode(encoded.result, method)
        assert decoded.status == "success", method
        assert decoded.result == source, method


def test_bytearray_decode_accepts_raw_list():
    decoded = engine.decode("[104, 97, 99, 107]", "bytearray")
    assert decoded.status == "success"
    assert decoded.result == "hack"


def test_morse_unknown_token_becomes_question_mark():
    decoded = engine.decode("... --- ... ........", "morse")
    assert decoded.status == "success"
    assert decoded.result == "SOS?"


def test_invalid_base64_returns_error():
    decoded = engine.decode("not-a-valid-base64", "base64")
    assert decoded.status == "error"
    assert decoded.message == "Geçerli bir Base64 metni bekleniyordu."


def test_invalid_math_expression_returns_error():
    decoded = engine.decode("104+foo+99", "math_expr")
    assert decoded.status == "error"
    assert "yalnızca '+' ile ayrılmış sayılar" in decoded.message


def test_invalid_bytearray_returns_error():
    decoded = engine.decode("exec(bytes([999]))", "bytearray")
    assert decoded.status == "error"
    assert "0-255" in decoded.message


def test_invalid_json_payload_returns_error():
    decoded = engine.decode('{"run": "print(1)"}', "json_payload")
    assert decoded.status == "error"
    assert '"exec" alanı' in decoded.message


def test_invalid_binary_returns_error():
    decoded = engine.decode("0101010X", "binary")
    assert decoded.status == "error"
    assert "0/1" in decoded.message
