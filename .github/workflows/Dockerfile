# Base Image
FROM python:3.9

# Set environment variables
ENV KAFKA_VERSION=3.6.0
ENV SCALA_VERSION=2.13
ENV KAFKA_HOME=/opt/kafka

# Install required packages
RUN apt-get update && apt-get install -y wget openjdk-17-jdk

# Download & extract Kafka
RUN wget https://archive.apache.org/dist/kafka/3.6.0/kafka_2.12-3.6.0.tgz && \
    tar -xzf kafka_2.12-3.6.0.tgz && \
    mv kafka_2.12-3.6.0 ${KAFKA_HOME} && \
    rm kafka_2.12-3.6.0.tgz

# Add Kafka bin to PATH
ENV PATH="${KAFKA_HOME}/bin:${PATH}"

# Install Python dependencies
COPY .github/workflows/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Kafka user management script
WORKDIR /app
COPY .github/workflows/manage_kafka_user.py .

# Default command (can be overridden in GitHub Actions)
CMD ["python", "manage_kafka_user.py"]
