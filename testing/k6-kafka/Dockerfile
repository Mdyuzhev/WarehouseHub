# k6 с расширением xk6-kafka для нагрузочного тестирования Kafka
# WH-208

# Stage 1: Сборка k6 с расширением xk6-kafka
FROM golang:1.24-alpine AS builder

RUN apk add --no-cache git
RUN go install go.k6.io/xk6/cmd/xk6@latest
RUN xk6 build --with github.com/mostafa/xk6-kafka@latest --output /k6

# Stage 2: Минимальный runtime образ
FROM alpine:3.19

RUN apk add --no-cache ca-certificates

COPY --from=builder /k6 /usr/bin/k6

WORKDIR /scripts

ENTRYPOINT ["k6"]
