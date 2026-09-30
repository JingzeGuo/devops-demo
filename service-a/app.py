import requests
from flask import Flask, request

app = Flask(__name__)


@app.route("/request")
def handle_request():
    mode = request.args.get("mode", "normal")

    response = requests.get(
        "http://service-b:5001/work",
        params={"mode": mode},
        timeout=5,
    )

    return {
        "service_b_status": response.status_code,
        "service_b_response": response.json(),
    }, response.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
