import os
import subprocess
import secrets
import string
from kafka import KafkaProducer
from kafka import KafkaConsumer

from cryptography.fernet import Fernet
import json
import base64


# Load environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_ADMIN_USER = os.getenv("KAFKA_ADMIN_USER")
KAFKA_ADMIN_PASSWORD = os.getenv("KAFKA_ADMIN_PASSWORD")
KAFKA_USER = os.getenv("KAFKA_USER")
KAFKA_PASSWORD = os.getenv("KAFKA_PASSWORD", "").strip()
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
ACCESS_LEVELS = os.getenv("ACCESS_LEVELS", "READ,WRITE").split(",")  # Default to READ,WRITE if empty
ACTION = os.getenv("ACTION")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")


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

    send_kafka_credentials()

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
# Load encryption key from env or generate a new one
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()  # Generate a new key
    print(f"🔑 Generated new encryption key: {ENCRYPTION_KEY}")

fernet = Fernet(ENCRYPTION_KEY)

def decrypt_password(encrypted_password):
    """Decrypts the password using Fernet encryption."""
    try:
        return fernet.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        print(f"❌ Error decrypting password: {e}")
        return None

def encrypt_password(password):
    """Encrypts a password using Fernet encryption."""
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypts an encrypted password."""
    return fernet.decrypt(encrypted_password.encode()).decode()

sasl_config = {
    "bootstrap_servers": KAFKA_BROKER,
    "security_protocol": "SASL_PLAINTEXT",
    "sasl_mechanism": "SCRAM-SHA-512",
    "sasl_plain_username": KAFKA_ADMIN_USER,
    "sasl_plain_password": KAFKA_ADMIN_PASSWORD
}
def consume_kafka_credentials():
    print("consume_kafka_credentials")
    """Consumes Kafka credentials and prints in JSON format."""
    consumer = KafkaConsumer(
        "credential_details",
        bootstrap_servers=KAFKA_BROKER,
        security_protocol="SASL_PLAINTEXT",
        sasl_mechanism="SCRAM-SHA-256",
        sasl_plain_username=KAFKA_ADMIN_USER,
        sasl_plain_password=KAFKA_ADMIN_PASSWORD,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8"))
    )

    print("📥 Waiting for messages from Kafka...")
    for message in consumer:
        credentials = message.value
        decrypted_password = decrypt_password(credentials["password"])

        if decrypted_password:
            output_json = {
                "user": credentials["user"],
                "password": decrypted_password,
                "topic": credentials["topic"],
                "access": credentials["access"]
            }

            print(json.dumps(output_json, indent=4))  # Pretty-print JSON output

def send_kafka_credentials():
    """Sends encrypted user credentials as a JSON message to Kafka topic `credential_details`."""
    producer = KafkaProducer(
        bootstrap_servers=sasl_config["bootstrap_servers"],
        security_protocol=sasl_config["security_protocol"],
        sasl_mechanism=sasl_config["sasl_mechanism"],
        sasl_plain_username=sasl_config["sasl_plain_username"],
        sasl_plain_password=sasl_config["sasl_plain_password"],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    encrypted_password = encrypt_password(KAFKA_PASSWORD)
    
    credentials_message = {
        "user": KAFKA_USER,
        "password": encrypted_password,  # Encrypted password
        "topic": KAFKA_TOPIC,
        "access": ACCESS_LEVELS
    }

    


    print(f"📤 Sending encrypted credentials to topic `credential_details`: {credentials_message}")

    producer.send("credential_details", credentials_message)
    producer.flush()
    print("✅ Encrypted credentials sent successfully!")


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
    if ACTION == "create":
        create_kafka_user()
    elif ACTION == "delete":
        delete_kafka_user()
    elif ACTION == "display":
        consume_kafka_credentials()        
    elif ACTION == "update_user_access":
        update_kafka_permissions()
    else:
        print("❌ Invalid action! Use 'create', 'delete', 'display', or 'update_user_access'.")

