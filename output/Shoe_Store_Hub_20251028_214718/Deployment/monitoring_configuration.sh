#!/bin/bash

# Configure monitoring using Prometheus
prometheus --config.file=prometheus.yml

# Verify monitoring dashboard is working
curl -X GET http://localhost:9090