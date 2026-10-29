# V3Net Registry

The central list of [V3Net](https://github.com/ViSiON-3/vision-3-bbs/tree/main/docs/sysop/v3net) message networks for [ViSiON/3 BBS](https://github.com/ViSiON-3/vision-3-bbs).

The registry browser in the ViSiON/3 config editor reads `registry.json` from this repository and lists the networks a sysop can join. The default registry URL is:

```
https://raw.githubusercontent.com/ViSiON-3/v3net-registry/main/registry.json
```

A BBS fetches the registry when the browser opens and caches it for an hour, so a change merged to `main` reaches sysops within about an hour.

## Format

```json
{
  "v3net_registry": "1.0",
  "updated": "2026-10-29",
  "networks": [
    {
      "name": "felonynet",
      "description": "Official ViSiON/3 BBS message network",
      "hub_url": "http://felonynet.org:8765",
      "hub_node_id": "8fdeba233bfdb2ee",
      "hub_pubkey_b64": "PG5yr5oAdmcKu3uO423drk618+P6a1Wz8zs9qaDBNao=",
      "coordinator_pubkey_b64": "PG5yr5oAdmcKu3uO423drk618+P6a1Wz8zs9qaDBNao="
    }
  ]
}
```

| Field | Description |
|---|---|
| `v3net_registry` | Format version. Always `"1.0"`. |
| `updated` | Date of the last change, `YYYY-MM-DD`. |
| `name` | Network name: lowercase letters, digits, `-` and `_`. Must be unique. |
| `description` | One line, shown in the registry browser. |
| `hub_url` | Base URL of the network's hub. |
| `hub_node_id` | The hub's node ID: the first 8 bytes of the SHA-256 of its public key, in hex (16 characters). |
| `hub_pubkey_b64` | The hub's ed25519 public key, in standard base64. |
| `coordinator_pubkey_b64` | The network coordinator's ed25519 public key, in standard base64. Leaves reject NALs signed by any other key. |

Leaves that join through the registry pin both public keys, so they don't have to trust the keys a hub serves on first contact ([vision-3-bbs#656](https://github.com/ViSiON-3/vision-3-bbs/issues/656)). If the hub also acts as the coordinator, the two keys are the same.

## Starting a new network

Any ViSiON/3 BBS can host a network. Turn on the hub in the config editor, then create the network with the Hub Setup Wizard under **V3Net Networking → 3. Networks**. See [Hosting a Hub](https://github.com/ViSiON-3/vision-3-bbs/blob/main/docs/sysop/v3net/configuration.md#hosting-a-hub). To serve the hub over HTTPS, see [V3Net Hub TLS Setup](https://github.com/ViSiON-3/vision-3-bbs/blob/main/docs/sysop/v3net/hub-tls.md).

You don't need to list a network here to run it: sysops can join by entering the hub URL and network name directly. List it here so that it shows up in every BBS's registry browser, and so that leaves joining from the registry get your keys from here instead of trusting the first keys the hub serves.

## Adding or updating a network

1. Get your hub's keys from the hub machine itself, or from its endpoints:
   - `GET <hub_url>/v3net/v1/<network>/info` returns `hub_node_id` and `hub_pubkey_b64`
   - `GET <hub_url>/v3net/v1/<network>/nal` returns `coordinator_pubkey_b64`

   Leaves trust whatever keys the registry publishes, so check them against the hub machine itself, especially if the hub serves plain HTTP.
2. Add or edit the entry in `registry.json` and set `updated` to today's date.
3. Run the validator:

   ```sh
   python3 scripts/validate.py
   ```

4. Open a pull request. CI runs the same validator on every push and pull request.

If a hub is rebuilt with a new key, update `hub_node_id` and both key fields together. Updating the registry does not move existing leaves to the new key: a leaf that pinned the old key rejects the new one and reports it, and each sysop has to replace or clear the pin in their `v3net.json`. Tell your sysops before you rotate a key.

## Running your own registry

A BBS can read a different registry, for example a private list for a group of boards. Serve a file in the same format from any HTTP(S) URL, then set **Registry URL** on the V3Net settings screen of the config editor (`registryUrl` in `configs/v3net.json`).

- A BBS reads only one registry, so a private registry replaces this one. Copy the entries you still want listed, such as felonynet, into your file.
- The file must be 1 MB or smaller.
- Serve it over HTTPS. Leaves pin the keys a registry publishes, so whoever can change the file in transit can choose which hub a leaf trusts.
- To check your file, run `python3 scripts/validate.py path/to/registry.json` from a clone of this repository.

## Validation

`scripts/validate.py` uses only the Python standard library. It checks that:

- the top level has `v3net_registry` set to `"1.0"` and a valid `updated` date
- every entry has all the fields above, no unknown fields, and a unique name
- `hub_url` is http(s) and `hub_node_id` is 16 lowercase hex characters
- both keys are base64 that decodes to a 32-byte ed25519 key
- `hub_pubkey_b64` derives `hub_node_id`
