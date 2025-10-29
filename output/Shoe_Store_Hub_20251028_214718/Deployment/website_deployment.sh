#!/bin/bash

# Deploy website using Docker
docker-compose up -d

# Verify website is deployed and working
curl -X GET http://localhost:80