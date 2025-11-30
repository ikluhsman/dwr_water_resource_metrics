# DWR Water Resources Metrics

Python flask app that exposes Prometheus-style time-series metrics from Colorado Division of Water Resources REST Web API.

## Installation

These Prometheus exporters are intended to run in Docker, however technically they can run under any Python 3 distribution.

### Dependencies

If installing using the Docker image build, the requirements.txt contains the needed dependencies that must be installed for the exporter to compile and run.

Dependencies are:

Flask
prometheus_client
PyYAML
requests
urllib3

If you're installing the exporter in another Python environment, ensure your host has these dependencies installed i.e. ```pip install prometheus_client```. If you're running in a Python virtual environment ensure the dependencies are installed there.

At that point you may run the exporter and connect to the metrics page at http://127.0.0.1:8001/metrics.

### Docker

#### Building the Image

Building the docker image is straight-forward and standard. Place all files in the same folder, and use compose to build the image using ```docker compose build```.

#### Docker File

You can run the image from the Docker file:

```bash
    docker run -d -p 8001:8001 -v ./dwr_gauges.yaml:/config/dwr_gauges.yaml ikluhsman/dwr_exporter:latest
```

#### Docker Compose

After building the image you can run it with docker compose:

```
dwr_exporter:
    build: ./
    image: ikluhsman/dwr_exporter:latest
    container_name: dwr_exporter
    ports:
      - "${HOST_IP}:8001:8001" # HOST_IP in env_file
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./dwr_gauges.yaml:/config/dwr_gauges.yaml
```

Adapt to portainer if you wish or whatever other containerization platform you use.

## Configuration

Configuration can be done using environment variables in a .env file, ensure you use environment variables in your docker image or compose file.

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| DWR_API_KEY | xxx | Request an API key from the [REST Web services page](https://dwr.state.co.us/rest/get/help#Datasets&#TelemetryStationsController&#gettingstarted&#jsonxml). |
| HOST_IP | 0.0.0.0 | IP for flask app to listen on. |
| DWR_MAX_WORKERS | 10 | How many gauges/threads to query at a time. |

### Gauges File dwr_gauges.yaml

The gauges file contains the data needed to query the API for each gauge that you want to pull metrics for. Gauges are designed to gather specific data, in particular the past 10 days of streamflow data for the specified gauge, in Cubic Feet Per second. API parameters are documented at the DWR page for Colorado's Decision Support System's [REST Services API page](https://dwr.state.co.us/rest/get/help#Datasets&#TelemetryStationsController&#gettingstarted&#jsonxml) under the [Telemetry Stations](https://dwr.state.co.us/rest/get/help#TelemetryStationsController) dataset.

You may request your own API and include it in the .env file.

## Usage

After the exporter is running access it using: http://127.0.0.1:8001/metrics, lining up your host address and port with the host and port selected as you ran the flask app.

You will get an html page displaying the exposed metrics for the exporter as defined in the gauges.yaml configuration file.

Metrics are Time-Series telemetry metrics that may be scraped using a tool such as Prometheus.

## Metrics
| Name | Description | Category | Type |
| :--- | :--- | :--- | :--- |
| python_gc_objects_collected_total | Objects collected during gc | Python | counter |
| python_gc_objects_uncollectable_total | Uncollectable objects found during GC | Python | counter |
| python_gc_collections_total | Number of times this generation was collected | Python | counter |
| python_info | Python platform information | Python | gauge |
| process_virtual_memory_bytes | Virtual memory size in bytes. | System | gauge |
| process_resident_memory_bytes | Resident memory size in bytes. | System | gauge |
| process_start_time_seconds | Start time of the process since unix epoch in seconds. | System | gauge |
| process_cpu_seconds_total | Total user and system CPU time spent in seconds. | System | counter |
| process_open_fds | Number of open file descriptors. | System | gauge |
| process_max_fds | Maximum number of open file descriptors. | System | gauge |
| dwr_streamflow_cfs | Gauge streamflow data in cubic feet per second. | DWR | gauge |
| dwr_exporter_scrape_success_total | Number of successful gauge fetches. | DWR | gauge |
| dwr_exporter_scrape_failure_total | Total number of failed gauge fetches | DWR | gauge |
| dwr_exporter_gauges_total | Total number of gauges configured for polling | DWR | gauge |
| dwr_exporter_scrape_duration_seconds | Time spent scraping all gauges | DWR | gauge |

