FROM debian:latest

RUN apt update && apt install -y wget && \
    wget https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian92-x86_64-100.0.1.deb &&\
    apt install -y ./mongodb-database-tools-debian92-x86_64-100.0.1.deb
CMD ["bash"]