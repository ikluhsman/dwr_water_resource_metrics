#!/usr/bin/env python3
from flask import Flask, Response
import requests
import os
import yaml
import time
from prometheus_client import Gauge, Counter, Summary, generate_latest, CONTENT_TYPE_LATEST
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

# Prometheus metrics
DWR_STREAMFLOW = Gauge(
    "dwr_streamflow_cfs",
    "Colorado DWR streamflow in cubic feet per second",
    ["gauge_id", "friendly_name", "location_name"]
)

SCRAPE_SUCCESS = Gauge(
    "dwr_exporter_scrape_success_total",
    "Number of successful gauge fetches"
)

SCRAPE_FAILURE = Gauge(
    "dwr_exporter_scrape_failure_total",
    "Total number of failed gauge fetches"
)

GAUGES_TOTAL = Gauge(
    "dwr_exporter_gauges_total",
    "Total number of gauges configured for polling"
)

SCRAPE_DURATION = Gauge(
    "dwr_exporter_scrape_duration_seconds",
    "Time spent scraping all gauges"
)

GAUGES_FILE = "/config/dwr_gauges.yaml"
MAX_WORKERS = int(os.getenv("DWR_MAX_WORKERS", 10))

# Global requests session with retry logic
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


def load_gauges():
    try:
        with open(GAUGES_FILE, "r") as f:
            gauges = yaml.safe_load(f)
        if not isinstance(gauges, list):
            raise ValueError("gauges.yaml must be a list")
        for g in gauges:
            if not isinstance(g, dict) or "id" not in g or "abbrev" not in g:
                raise ValueError(f"Malformed gauge entry: {g}")
        return gauges
    except Exception as e:
        print(f"[ERROR] Loading gauges.yaml: {e}")
        return []


def fetch_dwr_gauge(abbrev: str):
    """Fetch latest discharge value from DWR telemetrytimeseriesraw"""
    url = (
        "https://dwr.state.co.us/Rest/GET/api/v2/telemetrystations/telemetrytimeseriesraw"
        f"?abbrev={abbrev}&min-modified=-10days&parameter=DISCHRG"
    )
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("ResultList", [])
        if results:
            latest_val = float(results[-1]["measValue"])
            return latest_val
    except Exception as e:
        print(f"[WARN] Error fetching DWR data for {abbrev}: {e}")
    return None


@app.route("/metrics")
def metrics():
    start_time = time.time()
    gauges = load_gauges()
    GAUGES_TOTAL.set(len(gauges))
    DWR_STREAMFLOW.clear()

    successes = 0
    failures = 0

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(gauges))) as executor:
        future_to_gauge = {executor.submit(fetch_dwr_gauge, g["abbrev"]): g for g in gauges}
        for future in as_completed(future_to_gauge):
            g = future_to_gauge[future]
            gauge_id = g.get("id")
            abbrev = g.get("abbrev")
            friendly = g.get("friendly_name", g.get("name", gauge_id))
            location_name = g.get("name", gauge_id)

            try:
                val = future.result()
                if val is not None:
                    successes += 1
                else:
                    failures += 1
                    val = float("nan")
            except Exception as e:
                print(f"[WARN] Error processing {gauge_id}: {e}")
                failures += 1
                val = float("nan")

            DWR_STREAMFLOW.labels(
                gauge_id=gauge_id,
                friendly_name=friendly,
                location_name=location_name
            ).set(val)

    SCRAPE_SUCCESS.set(successes)
    SCRAPE_FAILURE.set(failures)
    SCRAPE_DURATION.set(time.time() - start_time)

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)

