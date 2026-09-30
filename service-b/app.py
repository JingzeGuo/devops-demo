import time

from flask import Flask, request

app = Flask(__name__)


@app.route("/work")
def work():
    mode = request.args.get("mode", "normal")

    if mode == "slow":
        time.sleep(1.5)

    if mode == "error":
        return {"status": "error"}, 500

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
