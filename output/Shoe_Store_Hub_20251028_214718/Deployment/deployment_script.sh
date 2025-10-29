#!/bin/bash

# Set up infrastructure using AWS
aws ec2 run-instances --image-id ami-abc123 --instance-type t2.micro --key-name my-key --security-group-ids sg-123456

# Deploy website using Docker
docker-compose up -d

# Configure monitoring using Prometheus
prometheus --config.file=prometheus.yml

# Verify website is deployed and working
curl -X GET http://localhost:80

# Verify monitoring dashboard is working
curl -X GET http://localhost:9090