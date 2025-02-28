# Base Image
FROM python:3.9

# Set environment variables
ENV KAFKA_VERSION=3.6.0
ENV SCALA_VERSION=2.13
ENV KAFKA_HOME=/opt/kafka

# Install required packages
RUN apt-get update && apt-get install -y wget openjdk-11-jdk

# Download & extract Kafka
RUN wget https://downloads.apache.org/kafka/${KAFKA_VERSION}/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz && \
    tar -xzf kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz && \
    mv kafka_${SCALA_VERSION}-${KAFKA_VERSION} ${KAFKA_HOME} && \
    rm kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz

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
