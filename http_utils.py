import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _build_url(url, params=None):
    if not params:
        return url
    return f"{url}?{urlencode(params, doseq=True)}"


def http_get_json(url, params=None, headers=None, timeout=10):
    request_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if headers:
        request_headers.update(headers)
    request = Request(_build_url(url, params), headers=request_headers, method="GET")
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def http_post_json(url, data, headers=None, timeout=10):
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if headers:
        request_headers.update(headers)

    body = json.dumps(data).encode("utf-8")
    request = Request(url, data=body, headers=request_headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)
