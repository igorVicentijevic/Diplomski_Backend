"""Lokalna stranica za rucno oznacavanje tona vesti.

Pokretanje:
    python -m experiments.tone_eval.serve_annotation --annotator igor

Otvori http://127.0.0.1:8777 i oznacavaj tasterima 1 / 2 / 3.
Odgovori se odmah upisuju u datasets/tone_labels_<annotator>.jsonl,
pa se oznacavanje moze prekidati i nastavljati.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATASETS = Path(__file__).parent / "datasets"
PAGE = Path(__file__).parent / "annotation" / "index.html"
VALID = {"positive", "neutral", "negative"}


class AnnotationStore:
    def __init__(self, annotator: str) -> None:
        self._path = DATASETS / f"tone_labels_{annotator}.jsonl"
        self._annotator = annotator
        self._labels: dict[str, str] = {}
        if self._path.exists():
            for line in self._path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                self._labels[record["item_id"]] = record["label"]

    @property
    def labels(self) -> dict[str, str]:
        return dict(self._labels)

    def save(self, item_id: str, label: str) -> None:
        if label not in VALID:
            raise ValueError(label)
        self._labels[item_id] = label
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "annotator": self._annotator,
                        "item_id": item_id,
                        "label": label,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def load_items() -> list[dict]:
    path = DATASETS / "tone_items.jsonl"
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_handler(store: AnnotationStore, items: list[dict]):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args) -> None:
            return

        def _send(self, payload: bytes, content_type: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send(
                    PAGE.read_bytes(),
                    "text/html; charset=utf-8",
                )
                return
            if parsed.path == "/items":
                payload = json.dumps(
                    {"items": items, "labels": store.labels},
                    ensure_ascii=False,
                ).encode("utf-8")
                self._send(payload, "application/json; charset=utf-8")
                return
            self.send_error(404)

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/label":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            try:
                store.save(body["item_id"], body["label"])
            except (KeyError, ValueError):
                self.send_error(400)
                return
            self._send(b'{"ok":true}', "application/json")

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator", required=True)
    parser.add_argument("--port", type=int, default=8777)
    arguments = parser.parse_args()

    items = load_items()
    store = AnnotationStore(arguments.annotator)
    handler = build_handler(store, items)
    server = ThreadingHTTPServer(("127.0.0.1", arguments.port), handler)
    print(f"ocenjivac: {arguments.annotator}")
    print(f"stavki: {len(items)}, vec oznaceno: {len(store.labels)}")
    print(f"otvori http://127.0.0.1:{arguments.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
