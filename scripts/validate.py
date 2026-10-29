#!/usr/bin/env python3
"""Validate registry.json against the V3Net registry format.

Checks the structure leaves expect (protocol.Registry / RegistryEntry in
vision-3-bbs) and that each published key is a raw ed25519 public key. The
hub key must also derive the entry's hub_node_id (first 8 bytes of its
SHA-256, hex), so a key can't be swapped without changing the node ID.
"""
import base64
import binascii
import datetime
import hashlib
import json
import re
import sys
import urllib.parse

REQUIRED = {
    "name": str,
    "description": str,
    "hub_url": str,
    "hub_node_id": str,
    "hub_pubkey_b64": str,
    "coordinator_pubkey_b64": str,
}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
NODE_ID_RE = re.compile(r"^[0-9a-f]{16}$")


def decode_key(value):
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None
    return raw if len(raw) == 32 else None


def valid_hub_url(value):
    try:
        url = urllib.parse.urlsplit(value)
        url.port  # raises ValueError for a non-numeric or out-of-range port
    except ValueError:
        return False
    return url.scheme in ("http", "https") and bool(url.hostname)


def validate(reg):
    errors = []
    if reg.get("v3net_registry") != "1.0":
        errors.append('v3net_registry must be "1.0"')
    try:
        datetime.date.fromisoformat(reg.get("updated", ""))
    except (TypeError, ValueError):
        errors.append("updated must be a YYYY-MM-DD date")
    networks = reg.get("networks")
    if not isinstance(networks, list) or not networks:
        return errors + ["networks must be a non-empty list"]

    seen = set()
    for i, net in enumerate(networks):
        where = f"networks[{i}]"
        if not isinstance(net, dict):
            errors.append(f"{where}: must be an object")
            continue
        where = f"networks[{i}] ({net.get('name', '?')})"
        bad = False
        for field, typ in REQUIRED.items():
            if not isinstance(net.get(field), typ) or not net[field]:
                errors.append(f"{where}: {field} is required")
                bad = True
        unknown = set(net) - set(REQUIRED)
        if unknown:
            errors.append(f"{where}: unknown fields {sorted(unknown)}")
        if bad:
            continue

        if not NAME_RE.match(net["name"]):
            errors.append(f"{where}: name must be lowercase [a-z0-9_-]")
        if net["name"] in seen:
            errors.append(f"{where}: duplicate network name")
        seen.add(net["name"])
        if not valid_hub_url(net["hub_url"]):
            errors.append(f"{where}: hub_url must be an http(s) URL with a host")
        if not NODE_ID_RE.match(net["hub_node_id"]):
            errors.append(f"{where}: hub_node_id must be 16 lowercase hex chars")

        hub_key = decode_key(net["hub_pubkey_b64"])
        if hub_key is None:
            errors.append(f"{where}: hub_pubkey_b64 is not a base64 ed25519 key")
        elif hashlib.sha256(hub_key).hexdigest()[:16] != net["hub_node_id"]:
            errors.append(f"{where}: hub_pubkey_b64 does not derive hub_node_id")
        if decode_key(net["coordinator_pubkey_b64"]) is None:
            errors.append(f"{where}: coordinator_pubkey_b64 is not a base64 ed25519 key")
    return errors


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "registry.json"
    try:
        with open(path) as f:
            reg = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"{path}: {e}", file=sys.stderr)
        return 1
    errors = validate(reg) if isinstance(reg, dict) else ["top level must be an object"]
    for e in errors:
        print(f"{path}: {e}", file=sys.stderr)
    if not errors:
        print(f"{path}: ok ({len(reg['networks'])} networks)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
