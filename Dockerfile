# Dockerfile for building multiple images

# Stage 1: Build etcd image
FROM quay.io/coreos/etcd:v3.5.5 as etcd
ENV ETCD_AUTO_COMPACTION_MODE=revision
ENV ETCD_AUTO_COMPACTION_RETENTION=1000
ENV ETCD_QUOTA_BACKEND_BYTES=4294967296
ENV ETCD_SNAPSHOT_COUNT=50000

# Stage 2: Build minio image
FROM minio/minio:RELEASE.2023-03-20T20-16-18Z as minio
ENV MINIO_ACCESS_KEY=minioadmin
ENV MINIO_SECRET_KEY=minioadmin

# Stage 3: Build standalone image
FROM milvusdb/milvus:v2.2.11 as standalone

# Stage 4: Build attu image
FROM zilliz/attu:v2.2.6 as attu
ENV MILVUS_URL=milvus-standalone:19530

# Final stage: Use ubuntu as the base image
FROM ubuntu:latest

# Install supervisor and create log directory
RUN apt-get update && apt-get install -y supervisor && mkdir -p /var/log/supervisor

# Copy supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy services from previous stages
COPY --from=etcd / /etcd/
COPY --from=minio / /minio/
COPY --from=standalone / /standalone/
COPY --from=attu / /attu/

# Define the command to run when the container starts
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
