import requests


FLARESOLVERR_URL = "http://localhost:8191/v1"


def fetch_with_flaresolverr(url, timeout=60000):
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": timeout,
    }

    response = requests.post(FLARESOLVERR_URL, json=payload)
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError("FlareSolverr failed")

    return data["solution"]["response"]
