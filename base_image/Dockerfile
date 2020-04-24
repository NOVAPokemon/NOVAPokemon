FROM mongo:latest

RUN mkdir /service
WORKDIR /service

COPY dockerize .
RUN chmod +x dockerize

COPY start_with_mongo.sh .
RUN chmod +x start_with_mongo.sh