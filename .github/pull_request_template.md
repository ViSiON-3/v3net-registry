## Network

<!-- Which network does this add or change, and why? For a key change, say why the key changed. -->

## Submitter checklist

- [ ] I run this network's hub, or I'm submitting it on the hub operator's behalf
- [ ] I took the keys from the hub machine itself, or compared them with what it reports
- [ ] I set `updated` to today's date
- [ ] `python3 scripts/validate.py` passes

## Reviewer checklist

- [ ] `hub_node_id` and `hub_pubkey_b64` match `<hub_url>/v3net/v1/<network>/info`
- [ ] `coordinator_pubkey_b64` matches `<hub_url>/v3net/v1/<network>/nal`
- [ ] The submitter's control of the hub is confirmed through a channel we already trust
- [ ] For a key change: the reason makes sense, and the network's sysops know they'll need to update their pins
