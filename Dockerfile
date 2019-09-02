FROM alpine:3.10 AS builder
ENV TRIVY_VERSION 0.1.6
RUN apk add --no-cache \
      curl \
      tar \
      tzdata
WORKDIR /tmp
RUN curl -L https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz -o trivy.tar.gz && \
    tar xzvf trivy.tar.gz

FROM docker:19-dind
RUN apk --no-cache add git python3
RUN pip3 install --no-cache-dir pipenv && \
    mkdir -p /app/ecranner
COPY --from=builder /tmp/trivy /usr/local/bin/trivy
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
RUN chmod +x /usr/local/bin/trivy

WORKDIR /app
COPY Pipfile* /app/
RUN pipenv install --system --clear --deploy
COPY ./ecranner.sh /ecranner.sh
RUN chmod +x /ecranner.sh
COPY ecranner /app/ecranner
ENTRYPOINT ["/ecranner.sh"]
