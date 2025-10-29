#!/bin/bash

# Verify monitoring dashboard is working
curl -s -f http://localhost:3000 | grep "Shoe Store Hub Monitoring Dashboard"

# Verify backup procedures are working
ls -l /var/backups/shoe_store_hub | grep "shoe_store_hub"

# Verify update protocol is working
ansible-playbook -i hosts update.yml