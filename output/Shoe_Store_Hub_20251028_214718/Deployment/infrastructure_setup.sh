#!/bin/bash

# Set up infrastructure using AWS
aws ec2 run-instances --image-id ami-abc123 --instance-type t2.micro --key-name my-key --security-group-ids sg-123456

# Configure security group
aws ec2 authorize-security-group-ingress --group-id sg-123456 --protocol tcp --port 80 --cidr 0.0.0.0/0