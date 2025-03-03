import os
import subprocess

# Load environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_ADMIN_USER = os.getenv("KAFKA_ADMIN_USER")
KAFKA_ADMIN_PASSWORD = os.getenv("KAFKA_ADMIN_PASSWORD")
KAFKA_USER = os.getenv("KAFKA_USER")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
ACTION = os.getenv("ACTION")
KAFKA_CONFIG_PATH = "/opt/kafka/bin/kafka-configs.sh"  # Path inside Docker
KAFKA_ACL_PATH = "/opt/kafka/bin/kafka-acls.sh"  # ACL management script

print("KAFKA_ADMIN_USER:", KAFKA_ADMIN_USER)
print("KAFKA_USER:", KAFKA_USER)

def execute_command(command):
    """Executes a shell command and prints the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {e.stderr}")

def create_kafka_user():
    """Creates a Kafka user with SCRAM-SHA-512 authentication using admin credentials."""
    print(f"🚀 Creating Kafka user: {KAFKA_USER}")

    command = f"""
    {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
    --alter --add-config "SCRAM-SHA-512=[iterations=4096,password={KAFKA_PASSWORD}]" \
    --entity-type users --entity-name {KAFKA_USER} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    execute_command(command)
    print(f" Kafka user {KAFKA_USER} created successfully!")

    # Grant access after user creation
    grant_kafka_permissions()

def delete_kafka_user():
    """Deletes a Kafka user using admin credentials."""
    print(f"Deleting Kafka user: {KAFKA_USER}")

    command = f"""
    {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
    --alter --delete-config "SCRAM-SHA-512" \
    --entity-type users --entity-name {KAFKA_USER} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    execute_command(command)
    print(f" Kafka user {KAFKA_USER} deleted successfully!")

    # Remove ACLs after user deletion
    revoke_kafka_permissions()

def grant_kafka_permissions():
    """Grants read and write access for the Kafka user on the topic."""
    print(f" Granting read/write permissions to {KAFKA_USER} on topic {KAFKA_TOPIC}...")

    command = f"""
    {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
    --add --allow-principal User:{KAFKA_USER} \
    --operation Read --operation Write \
    --topic {KAFKA_TOPIC} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    execute_command(command)
    print(f" Read/write permissions granted to {KAFKA_USER} on {KAFKA_TOPIC}!")

def revoke_kafka_permissions():
    """Revokes read and write access for the Kafka user on the topic."""
    print(f" Revoking permissions for {KAFKA_USER} on topic {KAFKA_TOPIC}...")

    command = f"""
    {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
    --remove --allow-principal User:{KAFKA_USER} \
    --operation Read --operation Write \
    --topic {KAFKA_TOPIC} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    execute_command(command)
    print(f" Permissions revoked for {KAFKA_USER} on {KAFKA_TOPIC}!")

if __name__ == "__main__":
    if ACTION == "create":
        create_kafka_user()
    elif ACTION == "delete":
        delete_kafka_user()
    else:
        print(" Invalid action! Use 'create' or 'delete'.")
