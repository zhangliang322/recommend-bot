from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_PDD_ENDPOINT = "https://gw-api.pinduoduo.com/api/router"


class PddConnectionError(RuntimeError):
    """A safe-to-display PDD connectivity error."""


@dataclass(frozen=True)
class PddCredentials:
    client_id: str
    client_secret: str
    pid: str


class PddClient:
    def __init__(
        self,
        credentials: PddCredentials,
        endpoint: str = DEFAULT_PDD_ENDPOINT,
        timeout: float = 10.0,
        max_attempts: int = 2,
    ) -> None:
        self.credentials = credentials
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_attempts = max(1, max_attempts)

    def _sign(self, parameters: dict[str, Any]) -> str:
        content = "".join(f"{key}{parameters[key]}" for key in sorted(parameters))
        raw = f"{self.credentials.client_secret}{content}{self.credentials.client_secret}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()  # noqa: S324

    def call(self, method: str, **parameters: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "client_id": self.credentials.client_id,
            "type": method,
            "timestamp": int(time.time()),
            "data_type": "JSON",
            **parameters,
        }
        payload["sign"] = self._sign(payload)
        request = Request(
            self.endpoint,
            data=urlencode(payload).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        result: Any = None
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                    result = json.loads(response.read().decode("utf-8"))
                break
            except Exception as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    time.sleep(0.25 * attempt)
        if last_error is not None and result is None:
            raise PddConnectionError("无法连接多多进宝接口，请检查网络和接口地址") from last_error
        if not isinstance(result, dict):
            raise PddConnectionError("多多进宝返回了无法识别的数据")
        error = result.get("error_response")
        if isinstance(error, dict):
            message = error.get("error_msg") or error.get("sub_msg") or "接口拒绝请求"
            raise PddConnectionError(f"多多进宝连接失败：{self._redact(str(message))}")
        return result

    def _redact(self, message: str) -> str:
        safe = message
        for secret in (
            self.credentials.client_id,
            self.credentials.client_secret,
            self.credentials.pid,
        ):
            if secret:
                safe = safe.replace(secret, "***")
        return safe[:300]

    def test_connection(self) -> dict[str, Any]:
        return self.search_goods("饰品", page=1, page_size=1)

    def search_goods(
        self, keyword: str, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        return self.call(
            "pdd.ddk.goods.search",
            keyword=keyword,
            page=page,
            page_size=page_size,
            pid=self.credentials.pid,
        )

    def promotion_url(self, goods_sign: str) -> dict[str, Any]:
        return self.call(
            "pdd.ddk.goods.promotion.url.generate",
            p_id=self.credentials.pid,
            goods_sign_list=json.dumps([goods_sign], ensure_ascii=False),
        )
