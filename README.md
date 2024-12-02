# Apache Kafka Installation Guide

## Overview
This guide explains how to deploy Apache Kafka using the Bitnami Helm chart in a Kubernetes cluster. This setup leverages Kubernetes-native scalability and management for Kafka brokers.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architectural Consideration](#architectural-consideration)
3. [Configurations](#configurations)  
4. [Installation Steps](#installation-steps)
5. [Testing Kafka](#testing-kafka)
6. [Reference](#reference)

---

## Prerequisites

1. ### Kubernetes Cluster  
   Ensure Kubernetes clusters are running across two different Data centers and kubectl is configures in both clusters

2. ### Helm  
   Install Helm (v3 or later):  
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
   ****

4. ### Bitnami Repository
```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
```
3. ### Loadbalancer 
   Ensure that static ip for kafka broker and controllers are available as those IPs will be used to expose broker and controller outside of od Kubernetes cluster by loadbalancer

## Architectural Consideration
1. #### Version
   KRAft will be used for kafka installation 
2. #### Data Replication  
   Data will be replicated synchronously across different data centers based on kafka stretched cluster architecture. Controllers acroiss both data centers will 
   be conntected based on exposed loadbalancer service of controller
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
  1. Need to set sslClientAuth value as none (as the authentication will be bases on SASL)
      ```bash
      external:
          containerPort: 9095
          protocol: SASL_PLAINTEXT
          name: EXTERNAL
          sslClientAuth: "none"
      ```
  3. Add secret name for authorization to interconnect between brokers
      ```bash
         kubectl create secret generic controller-secret --from-literal=controller-password=admin -n kafka
         kubectl create secret generic interbroker-secret --from-literal=inter-broker-password=admin  -n kafka
         kubectl create secret generic kafka-controller-cluster-user-passwords --from-literal=client-passwords=admin --from-literal=inter-broker-password=admin --         from-literal=inter-broker-client-secret=interbroker-secret --from-literal=controller-password=admin --from-literal=controller-client-secret=controller-         secret -n kafka

        interbroker:
             user: admin
             password: admin
             clientId: inter_broker_client
             clientSecret: interbroker-secret

         controller:
             user: admin
             password: admin
             clientId: controller_broker_client
             clientSecret: controller-secret
      ```
   4. ##### Extra Listener:
      Add extra listener in extraListener section of values.xml
      ```bash
      extraListeners: 
        - name: CUSTOM
          containerPort: 9097
          protocol: PLAINTEXT
          sslClientAuth: "none" 
       ```
   5. Add security protocol of the listener
      ```bash
        securityProtocolMap:"CONTROLLER:SASL_PLAINTEXT,INTERNAL:SASL_PLAINTEXT,CUSTOM:PLAINTEXT,CLIENT:SASL_PLAINTEXT,EXTERNAL:SASL_PLAINTEXT,PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL" 
      ```   
### Service
1. Add service as LoadBalancer for both controller and broker
2.	Add Load balancer IP for both both broker and controller
3.	Add extra ports for extra listener
    
```bash
externalAccess:
  enabled: true
  .
  .
  .  
  controller:
    service:
      type: LoadBalancer
      ports:
        external: 29092
      loadBalancerClass: ""
      loadBalancerIPs: 
        - 34.56.35.87
      loadBalancerNames: []
      loadBalancerAnnotations: []
      loadBalancerSourceRanges: []
      allocateLoadBalancerNodePorts: true         
  broker:
    service:
      type: LoadBalancer
      ports:
        external: 9095
      loadBalancerClass: ""
      loadBalancerIPs: 
        - 34.27.186.200
        - 34.66.24.154
      loadBalancerNames: []
      loadBalancerAnnotations: []
      loadBalancerSourceRanges: []
    
      extraPorts: 
       - name: tcp-custom
         port: 9097
         protocol: TCP
         targetPort: 9097
    .
    .
    .   
```
#### Authentication and Authorizaton
   1. Add SASL as authentication and PLAINTEXT as encryption. So security protocol for corresponding listener (external) will be SASL_PLAINTEXT
   ```bash
     external:
       containerPort: 9095
       protocol: SASL_PLAINTEXT
       name: EXTERNAL
       sslClientAuth: "none"
 ```
  2. Need to add following configuration for custom authenticator and authorizer
  ```bash
  extraConfig: |
    broker.rack=dc1
    authorizer.class.name=org.apache.kafka.metadata.authorizer.CustomAuthorizer
    listener.name.external.plain.sasl.server.callback.handler.class=com.middleware.kafka.auth.LdapAuthenticateCallbackHandler
    ldap.url=ldap://ldap.exampledomain.com:389
    ldap.user=cn=admin,dc=exampledomain,dc=com
    ldap.password=adminpassword    
    allow.everyone.if.no.acl.found=false
    super.users=User:admin
   
   ```
#### Metadata
   1.	Provide value in clusterId field. This can be any value
   2.	Provide value in controllerQuorumVoters. This field will have all controller address across K8 cluster. The value will be all controller address with port and minid (which is id of controller ) Format like <<minid>>@<controller ip>:<<controller port>>
    Example:
   ```bash
  kraft:
    enabled: true
    existingClusterIdSecret: ""
    clusterId: "2365172653715237"
    controllerQuorumVoters: "1@34.56.35.87:29092,2@34.66.24.154:29092"
```
#### Metrics
1. Enable JMX service
   ```bash
   jmx:
    enabled: true
   ```   

#### Kafka Broker 
 1. Change MinID and replicacount  for both controller and broker as desired (MinID is starting point of broker id, so based in replication count assign MinID for controller and broker)
    ```bash
    controller:
       replicaCount: 1
       controllerOnly: true
       minId: 3

    broker:
        replicaCount: 2
        minId: 4
    ```

## Installation Steps
 1. Create separate namespace for kafka
  ```bash
     kubectl create ns kafka
  ```

2. Install kafka in both cluster using below command 
```bash
  helm install kafka-cluster bitnami/kafka –namespace kafka –values dc1-kafka-values.yaml or dc2-kafka-values.yaml
```
## Testing Kafka
  Below are few commands to verify ACl, topic 
  ```bash
   #SASL
export BOOTSTRAP_SERVER=34.27.186.200:9095,34.66.24.154:9095
##PLAINTEXT
export BOOTSTRAP_SERVER=34.55.229.28:9097,35.225.25.157:9097

--------------------- ACL Check -----------------------------------------------

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config ./client.properties --list 

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER   --add --allow-principal User:ANONYMOUS   --operation ALL   --topic '*' --command-config client.properties 
./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER   --add --allow-principal User:ANONYMOUS   --operation ALL   --group  '*' --command-config client.properties 

# add authorization
./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --add --allow-principal User:sujit --operation ALL --topic test11

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --add --allow-principal User:sujit --operation ALL --topic

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --add --allow-principal User:sujit --operation All --cluster 
./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --add --allow-principal User:sujit --operation READ --group  '*'

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --list --topic test11

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --list

./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --remove --allow-principal User:sujit --operation All --cluster 
./bin/kafka-acls.sh --bootstrap-server $BOOTSTRAP_SERVER --command-config client.properties --remove --allow-principal User:sujit --operation ALL --topic test11

---------------------------------------------------------------------------------------------

# add new user
----------------------------------------- User Management ------------------------------------------------------------------

./bin/kafka-configs.sh  --bootstrap-server $BOOTSTRAP_SERVER  --describe  --entity-type users  --command-config ./client.properties

./bin/kafka-configs.sh --bootstrap-server $BOOTSTRAP_SERVER  --alter --add-config 'SCRAM-SHA-256=[password=user_1]' --entity-type users --entity-name user_1 --command-config ./client.properties


./bin/kafka-configs.sh --bootstrap-server $BOOTSTRAP_SERVER --alter --delete-config "SCRAM-SHA-256" --entity-type users --entity-name user_1 --command-config ./client.properties

./bin/kafka-configs.sh --bootstrap-server $BOOTSTRAP_SERVER  --alter --add-config 'SCRAM-SHA-256=[password=123456]' --entity-type users --entity-name sujit --command-config ./client.properties

./bin/kafka-configs.sh --bootstrap-server $BOOTSTRAP_SERVER  --alter --add-config 'SCRAM-SHA-256=[password=123456]' --entity-type users --entity-name sujit_1 --command-config ./client.properties

--------------------------------------------------------------------------------------------------------------------------------------------
# create new topic
./bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER --create --topic test11 --partitions=2 --replication-factor=2 --command-config client.properties

./bin/kafka-topics.sh --bootstrap-server $BOOTSTRAP_SERVER --list --command-config client.properties
  ```

## Reference 
[Bitnami Kafka Helm Chart](https://bitnami.com/stack/kafka/helm)
