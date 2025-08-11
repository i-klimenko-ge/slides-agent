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
        if resp.ok:
            data = resp.json()
            print("Responses:", data.get("responses"))
            print("Current slide:", data.get("current_slide"))
        else:
            print("Error:", resp.status_code, resp.text)


if __name__ == "__main__":
    main()
