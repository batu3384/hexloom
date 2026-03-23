"""Core transformation logic for Hexloom."""

from __future__ import annotations

import ast
import base64
import binascii
import codecs
import functools
import html
import json
import re
from dataclasses import asdict, dataclass
from typing import Callable
from urllib.parse import quote, unquote


MORSE_MAP = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "'": ".----.",
    "!": "-.-.--",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    "&": ".-...",
    ":": "---...",
    ";": "-.-.-.",
    "=": "-...-",
    "+": ".-.-.",
    "-": "-....-",
    "_": "..--.-",
    '"': ".-..-.",
    "$": "...-..-",
    "@": ".--.-.",
}
REVERSE_MORSE_MAP = {value: key for key, value in MORSE_MAP.items()}


class TransformationError(Exception):
    """Raised when a transformation cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class MethodDescriptor:
    key: str
    label: str
    description: str
    category: str
    encode_title: str
    decode_title: str
    encode_input_label: str
    decode_input_label: str
    encode_output_label: str
    decode_output_label: str
    encode_placeholder: str
    decode_placeholder: str
    encode_example: str
    decode_example: str


@dataclass(slots=True)
class TransformationResult:
    status: str
    result: str | None
    clipboard_ready: bool
    message: str | None = None


@dataclass(slots=True)
class TransformationHealthItem:
    method: str
    label: str
    sample: str
    encoded_preview: str | None
    status: str
    message: str | None = None


def _guard(default_message: str) -> Callable[[Callable[..., str]], Callable[..., str]]:
    def decorator(func: Callable[..., str]) -> Callable[..., str]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> str:
            try:
                return func(*args, **kwargs)
            except TransformationError:
                raise
            except Exception as exc:
                raise TransformationError(default_message) from exc

        return wrapper

    return decorator


class TransformationEngine:
    """Encode/decode strings using multiple transformation families."""

    _BYTEARRAY_PATTERNS = (
        re.compile(r"^\s*exec\s*\(\s*bytes\s*\(\s*(\[[^\]]*\])\s*\)\s*\)\s*$", re.DOTALL),
        re.compile(r"^\s*bytes\s*\(\s*(\[[^\]]*\])\s*\)\s*$", re.DOTALL),
        re.compile(r"^\s*(\[[^\]]*\])\s*$", re.DOTALL),
    )
    _INVALID_PERCENT_PATTERN = re.compile(r"%(?![0-9A-Fa-f]{2})")

    def __init__(self) -> None:
        self._descriptors = [
            MethodDescriptor(
                "base64",
                "Base64",
                "Encodes plain text as a single-layer Base64 string.",
                "Web Encoding",
                "Encode text to Base64",
                "Decode Base64 to text",
                "Source text",
                "Base64 input",
                "Base64 output",
                "Decoded text",
                "Example: Hello World",
                "Example: SGVsbG8gV29ybGQ=",
                "Hello World",
                "SGVsbG8gV29ybGQ=",
            ),
            MethodDescriptor(
                "base64_double",
                "Base64 Double",
                "Applies Base64 twice or decodes a double-layer Base64 payload.",
                "Web Encoding",
                "Encode text to double Base64",
                "Decode double Base64 to text",
                "Source text",
                "Double Base64 input",
                "Double Base64 output",
                "Decoded text",
                "Example: Hello World",
                "Example: U0dWc2JHOGdWMjl5YkdRPQ==",
                "Hello World",
                "U0dWc2JHOGdWMjl5YkdRPQ==",
            ),
            MethodDescriptor(
                "bytearray",
                "Bytearray",
                "Builds a safe exec(bytes([...])) template or decodes raw byte values back to text.",
                "Payload",
                "Encode text to a bytearray template",
                "Decode a bytearray template to text",
                "Source text",
                "Bytearray input",
                "Bytearray output",
                "Decoded text",
                "Example: print('hello')",
                "Example: exec(bytes([112, 114, 105, 110, 116, 40, 39, 104, 101, 108, 108, 111, 39, 41]))",
                "print('hello')",
                "exec(bytes([112, 114, 105, 110, 116, 40, 39, 104, 101, 108, 108, 111, 39, 41]))",
            ),
            MethodDescriptor(
                "html_entities",
                "HTML Entities",
                "Converts text to numeric HTML entities or decodes entity content back to text.",
                "Markup",
                "Encode text as HTML entities",
                "Decode HTML entities to text",
                "Source text",
                "HTML entity input",
                "Entity output",
                "Decoded text",
                "Example: <b>hello</b>",
                "Example: &#60;&#98;&#62;&#104;&#101;&#108;&#108;&#111;&#60;&#47;&#98;&#62;",
                "<b>hello</b>",
                "&#60;&#98;&#62;&#104;&#101;&#108;&#108;&#111;&#60;&#47;&#98;&#62;",
            ),
            MethodDescriptor(
                "math_expr",
                "Math Expression",
                "Represents each character as a Unicode number joined with '+', then decodes with safe parsing.",
                "Numeric",
                "Encode text as a math expression",
                "Decode a math expression to text",
                "Source text",
                "Numeric input",
                "Numeric output",
                "Decoded text",
                "Example: Hello",
                "Example: 72+101+108+108+111",
                "Hello",
                "72+101+108+108+111",
            ),
            MethodDescriptor(
                "rot13",
                "ROT13",
                "Applies the classic 13-letter rotation; the same operation works in both directions.",
                "Classic Cipher",
                "Encode text with ROT13",
                "Decode ROT13 to text",
                "Source text",
                "ROT13 input",
                "ROT13 output",
                "Decoded text",
                "Example: Hello World",
                "Example: Uryyb Jbeyq",
                "Hello World",
                "Uryyb Jbeyq",
            ),
            MethodDescriptor(
                "url_encode",
                "URL Encode",
                "Generates URL-safe percent encoding or decodes a percent-encoded payload.",
                "Web Encoding",
                "Encode text for URLs",
                "Decode URL-encoded text",
                "Source text",
                "URL-encoded input",
                "URL-encoded output",
                "Decoded text",
                "Example: https://example.com/a b?x=1&y=2",
                "Example: https%3A%2F%2Fexample.com%2Fa%20b%3Fx%3D1%26y%3D2",
                "https://example.com/a b?x=1&y=2",
                "https%3A%2F%2Fexample.com%2Fa%20b%3Fx%3D1%26y%3D2",
            ),
            MethodDescriptor(
                "json_payload",
                "JSON Payload",
                'Wraps text in a {"exec": "..."} payload or extracts text from that JSON structure.',
                "Payload",
                "Encode text as a JSON payload",
                "Decode a JSON payload to text",
                "Source text",
                "JSON payload input",
                "JSON payload output",
                "Decoded text",
                'Example: console.log("hello")',
                'Example: {"exec": "console.log(\\"hello\\")"}',
                'console.log("hello")',
                '{"exec": "console.log(\\"hello\\")"}',
            ),
            MethodDescriptor(
                "morse",
                "Morse Code",
                "Uses the international Morse dictionary and returns '?' for unknown characters or tokens.",
                "Signal",
                "Encode text as Morse code",
                "Decode Morse code to text",
                "Source text",
                "Morse input",
                "Morse output",
                "Decoded text",
                "Example: SOS 2026",
                "Example: ... --- ... / ..--- ----- ..--- -....",
                "SOS 2026",
                "... --- ... / ..--- ----- ..--- -....",
            ),
            MethodDescriptor(
                "hex",
                "Hexadecimal",
                "Transforms UTF-8 bytes into hexadecimal or decodes hexadecimal text back to UTF-8.",
                "Numeric",
                "Encode text as hexadecimal",
                "Decode hexadecimal to text",
                "Source text",
                "Hex input",
                "Hex output",
                "Decoded text",
                "Example: Hello world",
                "Example: 48656c6c6f20776f726c64",
                "Hello world",
                "48656c6c6f20776f726c64",
            ),
            MethodDescriptor(
                "binary",
                "Binary",
                "Represents UTF-8 bytes as 8-bit blocks or decodes binary blocks back to text.",
                "Numeric",
                "Encode text as binary",
                "Decode binary to text",
                "Source text",
                "Binary input",
                "Binary output",
                "Decoded text",
                "Example: Binary ✓",
                "Example: 01000010 01101001 01101110 01100001 01110010 01111001 00100000 11100010 10011100 10010011",
                "Binary ✓",
                "01000010 01101001 01101110 01100001 01110010 01111001 00100000 11100010 10011100 10010011",
            ),
        ]
        self._registry: dict[str, dict[str, Callable[[str], str]]] = {
            "base64": {"encode": self._encode_base64, "decode": self._decode_base64},
            "base64_double": {
                "encode": self._encode_base64_double,
                "decode": self._decode_base64_double,
            },
            "bytearray": {"encode": self._encode_bytearray, "decode": self._decode_bytearray},
            "html_entities": {
                "encode": self._encode_html_entities,
                "decode": self._decode_html_entities,
            },
            "math_expr": {"encode": self._encode_math_expr, "decode": self._decode_math_expr},
            "rot13": {"encode": self._encode_rot13, "decode": self._decode_rot13},
            "url_encode": {"encode": self._encode_url, "decode": self._decode_url},
            "json_payload": {"encode": self._encode_json_payload, "decode": self._decode_json_payload},
            "morse": {"encode": self._encode_morse, "decode": self._decode_morse},
            "hex": {"encode": self._encode_hex, "decode": self._decode_hex},
            "binary": {"encode": self._encode_binary, "decode": self._decode_binary},
        }

    def available_methods(self) -> list[dict[str, str]]:
        return [asdict(descriptor) for descriptor in self._descriptors]

    def example_samples(self) -> dict[str, str]:
        return {descriptor.key: descriptor.encode_example for descriptor in self._descriptors}

    def is_supported(self, method: str) -> bool:
        return method in self._registry

    def encode(self, data: str, method: str) -> TransformationResult:
        return self._run("encode", data, method)

    def decode(self, data: str, method: str) -> TransformationResult:
        return self._run("decode", data, method)

    def run_self_check(self) -> dict[str, object]:
        results: list[TransformationHealthItem] = []
        all_ok = True

        for descriptor in self._descriptors:
            sample = descriptor.encode_example
            encoded = self.encode(sample, descriptor.key)
            if encoded.status != "success" or encoded.result is None:
                all_ok = False
                results.append(
                    TransformationHealthItem(
                        method=descriptor.key,
                        label=descriptor.label,
                        sample=sample,
                        encoded_preview=None,
                        status="error",
                        message=encoded.message or "Encode step failed.",
                    )
                )
                continue

            decoded = self.decode(encoded.result, descriptor.key)
            if decoded.status != "success" or decoded.result != sample:
                all_ok = False
                results.append(
                    TransformationHealthItem(
                        method=descriptor.key,
                        label=descriptor.label,
                        sample=sample,
                        encoded_preview=encoded.result[:120],
                        status="error",
                        message=decoded.message or "Decode step could not reproduce the sample payload.",
                    )
                )
                continue

            batch_outputs = [self.encode(sample, descriptor.key), self.encode(sample, descriptor.key)]
            batch_ok = all(item.status == "success" for item in batch_outputs)
            if not batch_ok:
                all_ok = False
                results.append(
                    TransformationHealthItem(
                        method=descriptor.key,
                        label=descriptor.label,
                        sample=sample,
                        encoded_preview=encoded.result[:120],
                        status="error",
                        message="Batch encode simulation failed.",
                    )
                )
                continue

            results.append(
                TransformationHealthItem(
                    method=descriptor.key,
                    label=descriptor.label,
                    sample=sample,
                    encoded_preview=encoded.result[:120],
                    status="success",
                    message="Encode, decode, and batch simulation passed.",
                )
            )

        return {
            "status": "ok" if all_ok else "error",
            "checked_methods": len(results),
            "success_count": sum(item.status == "success" for item in results),
            "error_count": sum(item.status == "error" for item in results),
            "results": [asdict(item) for item in results],
        }

    def _run(self, operation: str, data: str, method: str) -> TransformationResult:
        if not self.is_supported(method):
            return TransformationResult(
                status="error",
                result=None,
                clipboard_ready=False,
                message=f"Bilinmeyen dönüşüm yöntemi: {method}",
            )

        handler = self._registry[method][operation]
        try:
            result = handler(data)
        except TransformationError as exc:
            return TransformationResult(
                status="error",
                result=None,
                clipboard_ready=False,
                message=str(exc),
            )

        return TransformationResult(status="success", result=result, clipboard_ready=True)

    @_guard("Base64 encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_base64(self, data: str) -> str:
        return base64.b64encode(data.encode("utf-8")).decode("ascii")

    @_guard("Geçerli bir Base64 metni bekleniyordu.")
    def _decode_base64(self, data: str) -> str:
        try:
            decoded = base64.b64decode(data.encode("ascii"), validate=True)
            return decoded.decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
            raise TransformationError("Geçerli bir Base64 metni bekleniyordu.") from exc

    @_guard("Double Base64 encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_base64_double(self, data: str) -> str:
        first_pass = self._encode_base64(data)
        return self._encode_base64(first_pass)

    @_guard("Geçerli bir Double Base64 metni bekleniyordu.")
    def _decode_base64_double(self, data: str) -> str:
        first_pass = self._decode_base64(data)
        return self._decode_base64(first_pass)

    @_guard("Bytearray şablonu üretilemedi.")
    def _encode_bytearray(self, data: str) -> str:
        byte_values = ", ".join(str(value) for value in data.encode("utf-8"))
        return f"exec(bytes([{byte_values}]))"

    @_guard("Bytearray ifadesi çözümlenemedi. Örnek: exec(bytes([104, 97]))")
    def _decode_bytearray(self, data: str) -> str:
        payload = self._extract_bytearray_payload(data)
        values = ast.literal_eval(payload)
        if not isinstance(values, list):
            raise TransformationError("Bytearray ifadesi bir liste olmalıdır.")

        normalized: list[int] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
                raise TransformationError("Bytearray yalnızca 0-255 aralığında tamsayılar içermelidir.")
            normalized.append(value)

        try:
            return bytes(normalized).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TransformationError("Bytearray UTF-8 olarak çözümlenemedi.") from exc

    @_guard("HTML entity encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_html_entities(self, data: str) -> str:
        return "".join(f"&#{ord(char)};" for char in data)

    @_guard("HTML entity decode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _decode_html_entities(self, data: str) -> str:
        return html.unescape(data)

    @_guard("Math expression üretilemedi.")
    def _encode_math_expr(self, data: str) -> str:
        return "+".join(str(ord(char)) for char in data)

    @_guard("Math expression yalnızca '+' ile ayrılmış sayılar içermelidir.")
    def _decode_math_expr(self, data: str) -> str:
        if not data.strip():
            return ""

        characters: list[str] = []
        for token in data.split("+"):
            normalized = token.strip()
            if not normalized or not normalized.isdigit():
                raise TransformationError("Math expression yalnızca '+' ile ayrılmış sayılar içermelidir.")
            value = int(normalized)
            if not 0 <= value <= 0x10FFFF:
                raise TransformationError("Math expression içinde geçersiz Unicode değeri bulundu.")
            characters.append(chr(value))
        return "".join(characters)

    @_guard("ROT13 işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_rot13(self, data: str) -> str:
        return codecs.encode(data, "rot_13")

    @_guard("ROT13 işlemi sırasında beklenmeyen bir hata oluştu.")
    def _decode_rot13(self, data: str) -> str:
        return codecs.encode(data, "rot_13")

    @_guard("URL encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_url(self, data: str) -> str:
        return quote(data, safe="")

    @_guard("Geçerli bir URL encoded metni bekleniyordu.")
    def _decode_url(self, data: str) -> str:
        if self._INVALID_PERCENT_PATTERN.search(data):
            raise TransformationError("Geçerli bir URL encoded metni bekleniyordu.")
        return unquote(data)

    @_guard("JSON payload üretilemedi.")
    def _encode_json_payload(self, data: str) -> str:
        return json.dumps({"exec": data}, ensure_ascii=False)

    @_guard('Geçerli bir JSON payload bekleniyordu. Örnek: {"exec": "..."}')
    def _decode_json_payload(self, data: str) -> str:
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as exc:
            raise TransformationError('Geçerli bir JSON payload bekleniyordu. Örnek: {"exec": "..."}') from exc

        if not isinstance(parsed, dict) or "exec" not in parsed:
            raise TransformationError('JSON payload içinde "exec" alanı bulunmalıdır.')
        if not isinstance(parsed["exec"], str):
            raise TransformationError('"exec" alanı metin olmalıdır.')
        return parsed["exec"]

    @_guard("Morse encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_morse(self, data: str) -> str:
        tokens: list[str] = []
        for char in data.upper():
            if char == " ":
                tokens.append("/")
            else:
                tokens.append(MORSE_MAP.get(char, "?"))
        return " ".join(tokens)

    @_guard("Morse decode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _decode_morse(self, data: str) -> str:
        if not data.strip():
            return ""

        characters: list[str] = []
        for token in data.split():
            if token == "/":
                characters.append(" ")
            else:
                characters.append(REVERSE_MORSE_MAP.get(token, "?"))
        return "".join(characters)

    @_guard("Hex encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_hex(self, data: str) -> str:
        return data.encode("utf-8").hex()

    @_guard("Geçerli bir hexadecimal metni bekleniyordu.")
    def _decode_hex(self, data: str) -> str:
        normalized = data.strip().replace(" ", "")
        if len(normalized) % 2 != 0:
            raise TransformationError("Hex metni çift uzunlukta olmalıdır.")
        try:
            return bytes.fromhex(normalized).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise TransformationError("Geçerli bir hexadecimal metni bekleniyordu.") from exc

    @_guard("Binary encode işlemi sırasında beklenmeyen bir hata oluştu.")
    def _encode_binary(self, data: str) -> str:
        return " ".join(f"{value:08b}" for value in data.encode("utf-8"))

    @_guard("Geçerli bir binary metni bekleniyordu.")
    def _decode_binary(self, data: str) -> str:
        normalized = data.strip()
        if not normalized:
            return ""

        if " " in normalized:
            groups = normalized.split()
        else:
            if len(normalized) % 8 != 0:
                raise TransformationError("Binary metni 8 bitlik bloklardan oluşmalıdır.")
            groups = [normalized[index : index + 8] for index in range(0, len(normalized), 8)]

        byte_values: list[int] = []
        for group in groups:
            if len(group) != 8 or any(char not in {"0", "1"} for char in group):
                raise TransformationError("Binary metni yalnızca 8 bitlik 0/1 blokları içermelidir.")
            byte_values.append(int(group, 2))

        try:
            return bytes(byte_values).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TransformationError("Binary içerik UTF-8 olarak çözümlenemedi.") from exc

    def _extract_bytearray_payload(self, data: str) -> str:
        for pattern in self._BYTEARRAY_PATTERNS:
            match = pattern.match(data)
            if match:
                return match.group(1)
        raise TransformationError("Bytearray ifadesi çözümlenemedi. Örnek: exec(bytes([104, 97]))")
