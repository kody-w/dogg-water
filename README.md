# dogg-water — a federated node of the global tick network

**Water, per tick: a versioned emergency-water procedure (boil, disinfect, filter,
store, rotate), paired with a live USGS river-gauge reading and how far it sits from
flood stage.**

This repo keeps its own append-only chain of rapp/1 frames in `water/`. Every half
hour a GitHub Action reads the current tick anchor from the spine at
[kody-w/dogg](https://github.com/kody-w/dogg) and appends one frame of this node's
outlook, referencing that tick — so this chain joins every other node's data on the
same clock. "Right now" APIs only serve the present; the network keeps every present.

## What it carries

Every frame's `payload.water` has two parts:

1. **`procedure`** — a versioned, BOOK-grade emergency water procedure (`version` +
   `steps[]`), not fetched from anywhere: it's a constant in `tools/collect.py` that
   only changes when a human edits it and bumps the version. It covers, in order:
   boiling (1 minute rolling, 3 minutes above 2000 m altitude), chemical disinfection
   with plain household bleach (8 drops/gallon clear water, 16 drops/gallon cloudy
   water, 30-minute wait), filtering cloudy water *before* disinfecting it (filtering
   alone is not enough), storage (1 gallon per person per day, 3-day/72-hour minimum),
   and rotation (replace stored water every 6 months).
2. **`gauge`** — a live reading from the USGS Water Services API for site `02336000`
   (Chattahoochee River at Atlanta, GA), gauge height in feet, alongside the
   NWS-published flood stage for that site (22 ft, a fixed reference constant, not a
   live reading) and the current reading as a percentage of flood stage.

## Why it matters offline / for heirlooms

Two very different kinds of water knowledge, on one clock: the *procedure* is timeless
survival knowledge that should still be legible with no internet at all — the kind of
thing that belongs printed out and kept in a go-bag, not just on a phone. Because it
rides the tick chain, every past frame is a dated, hash-verified snapshot of exactly
what the procedure said at that moment — a durable version history, not a page that
silently changes under you. The *gauge* is the opposite: perishable, right-now river
state that only means something paired with a timestamp and a flood-stage reference.
Putting both in the same frame ties evergreen preparedness knowledge to a real,
falsifiable measurement of current conditions — a heirloom document with a live pulse.

## Precision and limits

- The procedure is general guidance for U.S. household emergency use — it is not
  medical advice, not a substitute for local public-health guidance during an actual
  contamination event, and it does not cover chemical, radiological, or heavy-metal
  contamination (boiling and bleach do not remove those).
- The gauge covers exactly one USGS site (02336000, Atlanta) — it is a sample point on
  one river, not a regional or national flood picture.
- `flood_stage_ft` is a fixed NWS-published reference constant baked into the code, not
  a live query — if NWS revises the official flood stage for this site, this node's
  constant needs a manual update to match.
- Readings are "instantaneous values" from USGS — provisional, subject to revision, and
  can lag or gap if USGS's own telemetry is down; a failed fetch shows up in
  `payload.sources_failed` rather than a stale number silently standing in.

**Verify it yourself:** `python3 tools/verify_thread.py` re-checks every frame with the
reference implementation from [kody-w/rapp-1](https://github.com/kody-w/rapp-1). CI runs
the same oracle on every push.

**Start your own node:** fork this repo, edit `THEME` / `STREAM` / `SOURCES` at the top
of `tools/collect.py` (keyless https APIs, small factual payloads, numbers as strings),
and enable the scheduled workflow. Your chain, your outlook, same clock — announce it on
the spine's registry ([kody-w/dogg](https://github.com/kody-w/dogg) issues) so agents
can find it.

## Trust

<!--trust-->
No ratings yet — used this chain? [Rate it](../../issues/new?template=rate.yml): valid ratings publish automatically as verifiable frames.
<!--/trust-->
