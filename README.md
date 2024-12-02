# Apache Kafka Installation Guide

## Overview
This guide explains how to deploy Apache Kafka using the Bitnami Helm chart in a Kubernetes cluster. This setup leverages Kubernetes-native scalability and management for Kafka brokers.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architectural Consideration](#architectural-consideration) 
3. [Installation Steps](#installation-steps)  
4. [Configuration](#configuration)
5. [Accessing Kafka](#kafka-access)
6. [Testing Kafka](#testing-kafka)  
7. [Troubleshooting](#troubleshooting)  
8. [Resources](#resources)

---

## Prerequisites

1. ### Kubernetes Cluster  
   Ensure Kubernetes clusters are running across two different Data centers and kubectl is configures in both clusters

2. ### Helm  
   Install Helm (v3 or later):  
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

3. ### Bitnami Repository
```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
```
3. ### Loadbalancer 
   Ensure that static ip for kafka broker and controllers are available as those IPs will be used to expose broker and controller outside of od kubernetes clsuter by loadbalancer

## Architectural Consideration
1. ## Version
     KRAft will be used for kafka installation 
2. ### Data Replication  
   Data will be replicated synchronously across different data centers based on kafka stretched cluster architecture. Controllers acroiss both data centers will be conntected based on exposed loadbalancer service of controller
3. ### Authentication
   Kafka will have security authentication for both SASL and PlainText. For SASL, Custom authentication will be implemented based on LDAP
4. ### Authorization
   Kafka will have ACL authorization.
6. ### Endpoint
   KAfka will have two enpoints. One endpoint will be based on SASL and another will be be based on PlainText for migration
