import os
import subprocess
import secrets
import string

# Load environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_ADMIN_USER = os.getenv("KAFKA_ADMIN_USER")
KAFKA_ADMIN_PASSWORD = os.getenv("KAFKA_ADMIN_PASSWORD")
KAFKA_USER = os.getenv("KAFKA_USER")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "").strip()  # Get and clean password
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
ACTION = os.getenv("ACTION")
KAFKA_CONFIG_PATH = "/opt/kafka/bin/kafka-configs.sh"  # Path inside Docker
KAFKA_ACL_PATH = "/opt/kafka/bin/kafka-acls.sh"  # ACL management script

print("KAFKA_ADMIN_USER:", KAFKA_ADMIN_USER)
print("KAFKA_USER:", KAFKA_USER)

def generate_password(length=16):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

# Auto-generate password if empty
if not KAFKA_PASSWORD:
    KAFKA_PASSWORD = generate_password()
    print(f" Generated password for {KAFKA_USER}: {KAFKA_PASSWORD}")

def execute_command(command):
    """Executes a shell command and prints the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f" Error executing command: {e.stderr}")

def create_kafka_user():
    """Creates a Kafka user with SCRAM-SHA-512 authentication using admin credentials."""
    print(f"🚀 Creating Kafka user: {KAFKA_USER}")

    command = f"""
    {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
    --alter --add-config "SCRAM-SHA-512=[iterations=4096,password={KAFKA_PASSWORD}]" \
    --entity-type users --entity-name {KAFKA_USER} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    print(f"Command to create user: {command}")  
    execute_command(command)
    print(f" Kafka user {KAFKA_USER} created successfully!")

    # Grant access after user creation
    grant_kafka_permissions()

def delete_kafka_user():
    """Deletes a Kafka user using admin credentials."""
    print(f" Deleting Kafka user: {KAFKA_USER}")

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
    print(f"Command to create grant: {command}") 
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

def get_kafka_user_credentials():
    """Retrieves Kafka user credentials (SCRAM-SHA-512) for a specific user or all users."""
    if KAFKA_USER:
        print(f" Fetching credentials for user: {KAFKA_USER}")
        command = f"""
        {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
        --describe --entity-type users --entity-name {KAFKA_USER} \
        --command-config /opt/kafka/config/admin_client.properties
        """
    else:
        print(f" Fetching credentials for all users")
        command = f"""
        {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
        --describe --entity-type users \
        --command-config /opt/kafka/config/admin_client.properties
        """

    execute_command(command)

def get_kafka_user_acls():
    """Retrieves Kafka ACLs for a specific user or all users."""
    if KAFKA_USER:
        print(f"🔍 Fetching ACLs for user: {KAFKA_USER}")
        command = f"""
        {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
        --list --principal User:{KAFKA_USER} \
        --command-config /opt/kafka/config/admin_client.properties
        """
    else:
        print(f" Fetching ACLs for all users")
        command = f"""
        {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
        --list --command-config /opt/kafka/config/admin_client.properties
        """

    execute_command(command)
    
if __name__ == "__main__":
    if ACTION == "create":
        create_kafka_user()
    elif ACTION == "delete":
        delete_kafka_user()
    elif ACTION == "display":
        get_kafka_user_credentials()
        get_kafka_user_acls()        
    else:
        print(" Invalid action! Use 'create' or 'delete' or 'display' .")
