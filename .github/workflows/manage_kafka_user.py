import os
import subprocess
import secrets
import string

# Load environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_ADMIN_USER = os.getenv("KAFKA_ADMIN_USER")
KAFKA_ADMIN_PASSWORD = os.getenv("KAFKA_ADMIN_PASSWORD")
KAFKA_USER = os.getenv("KAFKA_USER")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "").strip()
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
ACCESS_LEVELS = os.getenv("ACCESS_LEVELS", "READ,WRITE").split(",")  # Default to READ,WRITE if empty
ACTION = os.getenv("ACTION")

KAFKA_CONFIG_PATH = "/opt/kafka/bin/kafka-configs.sh"
KAFKA_ACL_PATH = "/opt/kafka/bin/kafka-acls.sh"

print("KAFKA_ADMIN_USER:", KAFKA_ADMIN_USER)
print("KAFKA_USER:", KAFKA_USER)

def generate_password(length=16):
    """Generates a random password if none is provided."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))

# Auto-generate password if empty
if not KAFKA_PASSWORD:
    KAFKA_PASSWORD = generate_password()
    print(f"🔑 Generated password for {KAFKA_USER}: {KAFKA_PASSWORD}")

def execute_command(command):
    """Executes a shell command and prints the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {e.stderr}")

def create_kafka_user():
    """Creates a Kafka user with SCRAM-SHA-512 authentication."""
    print(f"🚀 Creating Kafka user: {KAFKA_USER}")

    command = f"""
    {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
    --alter --add-config "SCRAM-SHA-512=[iterations=4096,password={KAFKA_PASSWORD}]" \
    --entity-type users --entity-name {KAFKA_USER} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    print(f"🔧 Command to create user: {command}")  
    execute_command(command)
    print(f"✅ Kafka user {KAFKA_USER} created successfully!")

    # Grant access after user creation
    grant_kafka_permissions()

def delete_kafka_user():
    """Deletes a Kafka user and revokes ACLs."""
    print(f"🗑️ Deleting Kafka user: {KAFKA_USER}")

    command = f"""
    {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
    --alter --delete-config "SCRAM-SHA-512" \
    --entity-type users --entity-name {KAFKA_USER} \
    --command-config /opt/kafka/config/admin_client.properties
    """

    execute_command(command)
    print(f"✅ Kafka user {KAFKA_USER} deleted successfully!")

    # Remove ACLs after user deletion
    revoke_kafka_permissions()

def grant_kafka_permissions():
    """Grants multiple access levels (READ, WRITE, etc.) to the user for the selected topic."""
    for access in ACCESS_LEVELS:
        access = access.strip().upper()  # Normalize input
        if access not in ["READ", "WRITE", "ALL"]:
            print(f"⚠️ Skipping invalid access level: {access}")
            continue

        print(f"🔐 Granting {access} access on topic '{KAFKA_TOPIC}' to user '{KAFKA_USER}'")
        command = f"""
        {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
        --add --allow-principal User:{KAFKA_USER} \
        --operation {access}  \
        --topic {KAFKA_TOPIC} \
        --command-config /opt/kafka/config/admin_client.properties
        """
        print(f"🔧 Command to grant access: {command}") 
        execute_command(command)

    print(f"✅ Permissions granted to {KAFKA_USER} on {KAFKA_TOPIC}!")

def revoke_kafka_permissions():
    """Revokes multiple access levels for the user."""
    for access in ACCESS_LEVELS:
        access = access.strip().upper()
        if access not in ["READ", "WRITE", "ALL"]:
            print(f"⚠️ Skipping invalid access level: {access}")
            continue

        print(f"🚫 Revoking {access} access on topic '{KAFKA_TOPIC}' from user '{KAFKA_USER}'")
        command = f"""
        {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
        --remove --allow-principal User:{KAFKA_USER} \
        --operation {access} \
        --topic {KAFKA_TOPIC} \
        --command-config /opt/kafka/config/admin_client.properties
        """
        execute_command(command)

def get_kafka_user_credentials():
    """Retrieves Kafka user credentials (SCRAM-SHA-512) for a specific user or all users."""
    if KAFKA_USER:
        print(f"🔍 Fetching credentials for user: {KAFKA_USER}")
        command = f"""
        {KAFKA_CONFIG_PATH} --bootstrap-server {KAFKA_BROKER} \
        --describe --entity-type users --entity-name {KAFKA_USER} \
        --command-config /opt/kafka/config/admin_client.properties
        """
    else:
        print(f"🔍 Fetching credentials for all users")
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
        print(f"🔍 Fetching ACLs for all users")
        command = f"""
        {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
        --list --command-config /opt/kafka/config/admin_client.properties
        """

    execute_command(command)
def update_kafka_permissions():
    """Updates ACLs for an existing Kafka user."""
    for access in ACCESS_LEVELS:
        access = access.strip().upper()
        if access not in ["READ", "WRITE", "ALL"]:
            print(f"⚠️ Skipping invalid access level: {access}")
            continue

        print(f"🔐 Granting {access} access on topic '{KAFKA_TOPIC}' to user '{KAFKA_USER}'")

        command = f"""
        {KAFKA_ACL_PATH} --bootstrap-server {KAFKA_BROKER} \
        --add --allow-principal User:{KAFKA_USER} \
        --operation {access} \
        --topic {KAFKA_TOPIC} \
        --command-config /opt/kafka/config/admin_client.properties
        """
        execute_command(command)

    print(f"✅ ACLs updated successfully for {KAFKA_USER}!")
if __name__ == "__main__":
