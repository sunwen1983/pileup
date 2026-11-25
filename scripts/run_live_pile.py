#!/usr/bin/env python3
"""Run the sample pile against an already-running server (dev only).

POSTs demo/pile-samples.json (real files, base64) to the server on
127.0.0.1:PORT with execute=true, then prints a compact summary:
transport, total cost, plan actions, conflicts, tool results.

Usage: python3 scripts/run_live_pile.py [--port 8000] [--no-execute]
"""
import argparse
import base64
import http.client
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "demo" / "samples"
MANIFEST = json.loads((ROOT / "demo" / "pile-samples.json").read_text())


def build_items():
    items = []
    for entry in MANIFEST["items"]:
        data = base64.b64encode(
            (SAMPLES / entry["filename"]).read_bytes()).decode()
        item = {"id": entry["id"], "kind": entry["kind"], "data": data,
                "mime": entry["mime"], "filename": entry["filename"]}
        if entry["kind"] == "audio":
            item["format"] = entry["format"]
        items.append(item)
    return items


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-execute", action="store_true")
    args = parser.parse_args()
    payload = {"items": build_items(), "execute": not args.no_execute}
    conn = http.client.HTTPConnection("127.0.0.1", args.port, timeout=300)
    conn.request("POST", "/api/run", body=json.dumps(payload),
                 headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    body = json.loads(resp.read())
    if resp.status != 200:
        print(f"server error {resp.status}: {body}", file=sys.stderr)
        return 1
    print(f"transport: {body['transport']}")
    print(f"total_cost_usd: {body['total_cost_usd']}")
    print(f"trace_file: {body['trace_file']}")
    print("items:")
    for item in body["items"]:
        extracted = item.get("extracted", {})
        dates = ", ".join(
            f"{d['text']} -> {d.get('iso')}"
            for d in extracted.get("dates", []))
        actions = ", ".join(
            f"{a['text']} (due {a.get('due')})"
            for a in extracted.get("actions", []))
        print(f"  - {item['id']}: type={item.get('type')} "
              f"confidence={item.get('confidence')}")
        print(f"    dates: {dates or '(none)'}")
        print(f"    actions: {actions or '(none)'}")
    print("plan actions:")
    for action in body["plan"]["actions"]:
        print(f"  - {action['text']} (due {action['due']}, "
              f"source {action['source']})")
    print("conflicts:")
    for conflict in body["plan"]["conflicts"]:
        print(f"  - {conflict['text']}")
    print("tool results:")
    for result in body["tool_results"] or []:
        print(f"  - {json.dumps(result, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
