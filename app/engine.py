"""Core transformation logic for Format Workbench."""

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
                "Düz metni tek katman Base64 string'ine dönüştürür.",
                "Web Encoding",
                "Metni Base64'e dönüştür",
                "Base64 içeriği metne çöz",
                "Kaynak metin",
                "Base64 içerik",
                "Base64 çıktı",
                "Çözülmüş metin",
                "Örnek: Hello World",
                "Örnek: SGVsbG8gV29ybGQ=",
                "Hello World",
                "SGVsbG8gV29ybGQ=",
            ),
            MethodDescriptor(
                "base64_double",
                "Base64 Double",
                "Metni iki kez Base64 katmanından geçirir veya iki katmanlı Base64 içeriği çözer.",
                "Web Encoding",
                "Metni çift Base64'e dönüştür",
                "Çift Base64 içeriği metne çöz",
                "Kaynak metin",
                "Double Base64 içerik",
                "Double Base64 çıktı",
                "Çözülmüş metin",
                "Örnek: Hello World",
                "Örnek: U0dWc2JHOGdWMjl5YkdRPQ==",
                "Hello World",
                "U0dWc2JHOGdWMjl5YkdRPQ==",
            ),
            MethodDescriptor(
                "bytearray",
                "Bytearray",
                "Metni güvenli bir exec(bytes([...])) şablonuna çevirir veya listedeki byte değerlerinden geri okur.",
                "Payload",
                "Metni bytearray şablonuna dönüştür",
                "Bytearray şablonunu metne çöz",
                "Kaynak metin",
                "Bytearray ifade",
                "exec(bytes([...])) çıktısı",
                "Çözülmüş metin",
                "Örnek: print('merhaba')",
                "Örnek: exec(bytes([112, 114, 105, 110, 116, 40, 39, 109, 101, 114, 104, 97, 98, 97, 39, 41]))",
                "print('merhaba')",
                "exec(bytes([112, 114, 105, 110, 116, 40, 39, 109, 101, 114, 104, 97, 98, 97, 39, 41]))",
            ),
            MethodDescriptor(
                "html_entities",
                "HTML Entities",
                "Metni sayısal HTML entity biçimine çevirir veya entity içeriğini çözer.",
                "Markup",
                "Metni HTML entity formatına dönüştür",
                "HTML entity içeriği metne çöz",
                "Kaynak metin",
                "HTML entity içerik",
                "Entity çıktı",
                "Çözülmüş metin",
                "Örnek: <b>merhaba</b>",
                "Örnek: &#60;&#98;&#62;&#109;&#101;&#114;&#104;&#97;&#98;&#97;&#60;&#47;&#98;&#62;",
                "<b>merhaba</b>",
                "&#60;&#98;&#62;&#109;&#101;&#114;&#104;&#97;&#98;&#97;&#60;&#47;&#98;&#62;",
            ),
            MethodDescriptor(
                "math_expr",
                "Math Expression",
                "Karakterleri Unicode sayılarıyla '+' üzerinden temsil eder; çözüm tarafında güvenli parse kullanır.",
                "Numeric",
                "Metni math expression'a dönüştür",
                "Math expression içeriği metne çöz",
                "Kaynak metin",
                "Sayı dizisi",
                "Sayısal expression",
                "Çözülmüş metin",
                "Örnek: Merhaba",
                "Örnek: 77+101+114+104+97+98+97",
                "Merhaba",
                "77+101+114+104+97+98+97",
            ),
            MethodDescriptor(
                "rot13",
                "ROT13",
                "Klasik 13 harf kaydırmalı dönüşümü uygular; aynı işlem iki yönde de aynıdır.",
                "Classic Cipher",
                "Metni ROT13 ile dönüştür",
                "ROT13 içeriği tekrar metne çevir",
                "Kaynak metin",
                "ROT13 içerik",
                "ROT13 çıktı",
                "Çözülmüş metin",
                "Örnek: Hello World",
                "Örnek: Uryyb Jbeyq",
                "Hello World",
                "Uryyb Jbeyq",
            ),
            MethodDescriptor(
                "url_encode",
                "URL Encode",
                "URL güvenli yüzde kodlaması üretir veya yüzde kodlu içeriği çözer.",
                "Web Encoding",
                "Metni URL encode et",
                "URL encoded içeriği metne çöz",
                "Kaynak metin",
                "URL encoded içerik",
                "Encoded URL çıktı",
                "Çözülmüş metin",
                "Örnek: https://example.com/a b?x=1&y=2",
                "Örnek: https%3A%2F%2Fexample.com%2Fa%20b%3Fx%3D1%26y%3D2",
                "https://example.com/a b?x=1&y=2",
                "https%3A%2F%2Fexample.com%2Fa%20b%3Fx%3D1%26y%3D2",
            ),
            MethodDescriptor(
                "json_payload",
                "JSON Payload",
                'Metni {"exec": "..."} şablonuna sarar veya bu JSON payload içinden metni geri alır.',
                "Payload",
                "Metni JSON payload'a dönüştür",
                "JSON payload içeriği metne çöz",
                "Kaynak metin",
                "JSON payload",
                "JSON çıktı",
                "Çözülmüş metin",
                'Örnek: console.log("merhaba")',
                'Örnek: {"exec": "console.log(\\"merhaba\\")"}',
                'console.log("merhaba")',
                '{"exec": "console.log(\\"merhaba\\")"}',
            ),
            MethodDescriptor(
                "morse",
                "Morse Code",
                "Uluslararası Morse eşlemesini kullanır; bilinmeyen karakterlerde veya tokenlarda '?' gösterir.",
                "Signal",
                "Metni Morse koduna dönüştür",
                "Morse kodunu metne çöz",
                "Kaynak metin",
                "Morse içerik",
                "Morse çıktı",
                "Çözülmüş metin",
                "Örnek: SOS 2026",
                "Örnek: ... --- ... / ..--- ----- ..--- -....",
                "SOS 2026",
                "... --- ... / ..--- ----- ..--- -....",
            ),
            MethodDescriptor(
                "hex",
                "Hexadecimal",
                "UTF-8 byte dizisini hex formata çevirir veya hex içeriği metne çözer.",
                "Numeric",
                "Metni hexadecimal'e dönüştür",
                "Hexadecimal içeriği metne çöz",
                "Kaynak metin",
                "Hex içerik",
                "Hex çıktı",
                "Çözülmüş metin",
                "Örnek: Merhaba dünya",
                "Örnek: 4d6572686162612064c3bc6e7961",
                "Merhaba dünya",
                "4d6572686162612064c3bc6e7961",
            ),
            MethodDescriptor(
                "binary",
                "Binary",
                "UTF-8 byte dizisini 8 bit bloklar halinde üretir veya binary içeriği geri çözer.",
                "Numeric",
                "Metni binary'e dönüştür",
                "Binary içeriği metne çöz",
                "Kaynak metin",
                "Binary içerik",
                "Binary çıktı",
                "Çözülmüş metin",
                "Örnek: Binary ✓",
                "Örnek: 01000010 01101001 01101110 01100001 01110010 01111001 00100000 11100010 10011100 10010011",
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
                        message=encoded.message or "Encode aşaması başarısız oldu.",
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
                        message=decoded.message or "Decode aşaması örnek veriyi geri üretemedi.",
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
                        message="Toplu encode simülasyonu başarısız oldu.",
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
                    message="Encode, decode ve batch simülasyonu başarılı.",
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
