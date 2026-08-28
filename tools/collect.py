#!/usr/bin/env python3
"""A federated tick-network node: this repo's own append-only chain, keyed to the
global tick spine at kody-w/dogg.

Every run reads the spine's current tick anchor, takes this node's themed snapshot of
keyless public APIs, and appends one frame referencing that tick. Different repos, run
by different people, each with their own outlook — all joinable on the tick key. To
start your own node: fork this repo, edit THEME/STREAM/SOURCES below, enable the
scheduled workflow. Frames verify with the reference implementation (tools/rapp.py,
from kody-w/rapp-1); CI re-verifies the whole chain on every push.
"""
import json, sys, pathlib, datetime, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import rapp as R
import chainio

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPINE_HEAD = "https://raw.githubusercontent.com/kody-w/dogg/main/ticks/HEAD.json"
TIMEOUT = 8

# ---- edit these three for your node -------------------------------------------------
THEME = "water"                       # also the data directory name
STREAM = "water:@kody-w/dogg-water"                    # your stream id (your repo, your name)
# SOURCES: name -> zero-arg callable returning a SMALL dict of facts.
# rapp/1 canonical hashing forbids floats: numeric facts ride as strings or ints.
# -------------------------------------------------------------------------------------

# NWS-published flood stage for USGS site 02336000 (Chattahoochee River at Atlanta).
# This is a published reference constant, not a live reading — noted, not fetched.
FLOOD_STAGE_FT = 22
USGS_SITE = "02336000"
USGS_SITE_NAME = "Chattahoochee River at Atlanta, GA"

# Versioned procedure document. Bump the version and append a changelog entry (below)
# any time the steps change — old frames keep the version they were minted under, so
# the chain itself is the audit trail of what advice was live at any given tick.
PROCEDURE_VERSION = 1
PROCEDURE_STEPS = [
    "Boil: bring water to a rolling boil for 1 minute. Above 2000 m (6560 ft) "
    "altitude, boil for 3 minutes instead — water boils at a lower temperature "
    "there, so it takes longer to kill pathogens.",
    "Chemical disinfection (if boiling isn't possible): use plain, unscented "
    "household bleach (5-9% sodium hypochlorite, no added scents or dyes). Add "
    "8 drops per gallon for clear water, 16 drops per gallon for cloudy water. "
    "Stir and let it stand 30 minutes before drinking.",
    "Filter first, then disinfect: if water is cloudy or has visible particles, "
    "filter it through a clean cloth, coffee filter, or settle-and-decant BEFORE "
    "boiling or bleaching. Filtering alone does not make water safe to drink.",
    "Storage: keep 1 gallon per person per day, with a 3-day (72-hour) minimum "
    "supply on hand per person. Use clean, food-grade, sealed containers stored "
    "in a cool, dark place away from direct sunlight and chemicals.",
    "Rotation: rotate stored water every 6 months. Date each container when "
    "filled so you always know what's due.",
]

def utc():
    n = datetime.datetime.now(datetime.timezone.utc)
    return n.strftime("%Y-%m-%dT%H:%M:%S.") + f"{n.microsecond // 1000:03d}Z"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"tick-node-{THEME}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())

def _gauge():
    d = get(f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={USGS_SITE}&parameterCd=00065")
    ts = d["value"]["timeSeries"][0]
    latest = ts["values"][0]["value"][-1]
    height = float(latest["value"])
    pct = height / FLOOD_STAGE_FT * 100
    return {
        "site": USGS_SITE,
        "site_name": USGS_SITE_NAME,
        "parameter": "Gage height, ft",
        "gauge_height_ft": latest["value"],
        "observed_local": latest["dateTime"],
        "flood_stage_ft": str(FLOOD_STAGE_FT),
        "flood_stage_source": "NWS",
        "pct_of_flood_stage": f"{pct:.1f}",
    }

SOURCES = {
    "procedure": lambda: {"version": PROCEDURE_VERSION, "steps": list(PROCEDURE_STEPS)},
    "gauge": _gauge,
}

def load_chain(d):
    return chainio.load_chain(d)

def main():
    spine = get(SPINE_HEAD)
    tick_n, tick_hash = spine["count"] - 1, spine["head_frame"]
    d = ROOT / THEME
    d.mkdir(exist_ok=True)
    chain = load_chain(d)
    head = chain[-1] if chain else None
    if head is not None and head["payload"].get("tick") == tick_n:
        print(f"{THEME}: tick {tick_n} already recorded — nothing to do")
        return
    data, failed = {}, []
    for name, fn in SOURCES.items():
        try:
            data[name] = fn()
        except Exception:
            failed.append(name)
    payload = {"tick": tick_n, "tick_frame": tick_hash, "spine": "kody-w/dogg",
               "fetched_utc": utc(), THEME: data, "sources_failed": failed}
    if head is None:
        payload["about"] = (f"A federated node of the global tick network: this repo's "
                            f"own {THEME} outlook, one frame per observed tick, keyed to "
                            "the spine's tick anchors so it joins every other node's "
                            "data on the same clock.")
    f = R.build_frame(f"{THEME}.snapshot", STREAM, (head["seq"] + 1) if head else 0,
                      utc(), payload, prev=(head["payload_hash"] if head else None))
    ok, step, why = R.verify_frame(f, head=head, stream_id_of_record=STREAM)
    if not ok:
        raise ValueError(f"refusing invalid frame: {step}: {why}")
    chainio.append_frame(d, f, STREAM)
    print(f"{THEME} frame {f['seq']} @ spine tick {tick_n}: {', '.join(data) or 'nothing'}"
          + (f" (failed: {', '.join(failed)})" if failed else ""))

if __name__ == "__main__":
    main()
