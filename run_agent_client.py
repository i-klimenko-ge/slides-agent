"""Simple CLI client to send text to the running FastAPI agent service."""

import requests

BASE_URL = "http://localhost:8000"


def main():
    url = f"{BASE_URL}/run-agent"
    while True:
        try:
            text = input("Enter text (or 'quit' to exit): ").strip()
        except EOFError:
            break
        if not text or text.lower() in {"quit", "exit"}:
            break
        resp = requests.post(url, json={"text": text})
        print("Status:", resp.status_code)


if __name__ == "__main__":
    main()
