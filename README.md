# Apache Kafka Installation Guide

## Overview
This guide explains how to deploy Apache Kafka using the Bitnami Helm chart in a Kubernetes cluster. This setup leverages Kubernetes-native scalability and management for Kafka brokers.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architectural Consideration](#architectural-consideration) 
3. [Configurations](#configuration)  
4. [Installation Steps](#installation-steps)
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
   curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

3. ### Bitnami Repository
```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
```
3. ### Loadbalancer 
   Ensure that static ip for kafka broker and controllers are available as those IPs will be used to expose broker and controller outside of od kubernetes clsuter by loadbalancer

## Architectural Consideration
1. #### Version
   KRAft will be used for kafka installation 
2. #### Data Replication  
   Data will be replicated synchronously across different data centers based on kafka stretched cluster architecture. Controllers acroiss both data centers will be conntected based on exposed loadbalancer service of controller
3. #### Authentication
   Kafka will have security authentication for both SASL and PlainText. For SASL, Custom authentication will be implemented based on LDAP
4. #### Authorization
   Kafka will have ACL authorization.
6. #### Endpoint
   KAfka will have two enpoints. One endpoint will be based on SASL and another will be be based on PlainText for migration
7. #### Broker and Controller
   Broker and Controller will have dedicated pod. It means there will be no pod act as controller and broker as well

## Configurations
Need to change in the helm chart configuration to adapt with the target architecture
#### Listener
  1. Need to set sslClientAuth value as none as the authentication will be bases on SASL
  2. Add secret name for authorization to interconnect between brokers
      ```bash
         kubectl create secret generic controller-secret --from-literal=controller-password=admin -n kafka
         kubectl create secret generic interbroker-secret --from-literal=inter-broker-password=admin  -n kafka
         kubectl create secret generic kafka-controller-cluster-user-passwords --from-literal=client-passwords=admin --from-literal=inter-broker-password=admin --         from-literal=inter-broker-client-secret=interbroker-secret --from-literal=controller-password=admin --from-literal=controller-client-secret=controller-         secret -n kafka
      ```
   3. ##### Extra Listener:
      Add extra listener in extraListener section of values.xml
      ```bash
      extraListeners: 
        - name: CUSTOM
          containerPort: 9097
          protocol: PLAINTEXT
          sslClientAuth: "none" 
       ```
   4. Add security protocol of the listener
      ```bash
        securityProtocolMap:"CONTROLLER:SASL_PLAINTEXT,INTERNAL:SASL_PLAINTEXT,CUSTOM:PLAINTEXT,CLIENT:SASL_PLAINTEXT,EXTERNAL:SASL_PLAINTEXT,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL" 
      ```   
### Service
#### Authentication and Authorizaton
#### Metadata
   1.	Provide value in clusterId field. This can be any value
   2.	Provide value in controllerQuorumVoters. This field will have all controller address across K8 cluster. The value will be all controller address with port and minid (which is id of controller ) Format like <<minid>>@<controller ip>:<<controller port>>
    Example:
   ```bash
  kraft:
    enabled: true
    existingClusterIdSecret: ""
    clusterId: "2365172653715237"
    controllerQuorumVoters: "1@34.56.35.87:29092"
```
#### Metrics


Create separate namespace for kafka (kubectl create ns kafka)
4.	Enable JMX service , if required
5.	Enable External Access service for controller and broker.
6.	Add service as LoadBalancer for both controller and broker
7.	Add Load balancer IP for both both broker and controller  
13.	Change desired replication count for both controller and broker
14.	Change MinID for both controller and broker as desired (MinID is starting point of broker id, so based in replication count assign MinID for controller and broker)

17.	Refer values.xml for both cluster   

18.	Install kafka in both cluster using below command 

helm install kafka-cluster bitnami/kafka –namespace kafka –values dc1-kafka-values.yaml or dc2-kafka-values.yaml

19.	Check target port of external service of controller. If port is not set correctly, edit the service and change the target port. 
20.	ACL Set up  We need to add the below configuration in kafka configuration where admin is super user
authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer
   allow.everyone.if.no.acl.found=false
   super.users=User:admin
   
21.	Add authentication as SASL and mechanism as SCRAM-SHA-256 and authentication as PLAINTEXT
      ```bash
      EXTERNAL:SASL_PLAINTEXT
      interBrokerMechanism: SCRAM-SHA-256
      controllerMechanism: SCRAM-SHA-256
       ```
22.	Listener:

b.	

   ```
c.	Add extra ports in service of kafka section
   ```bash
     extraPorts: 
       - name: tcp-custom
         port: 9097
         protocol: TCP
         targetPort: 9097
    ```     
