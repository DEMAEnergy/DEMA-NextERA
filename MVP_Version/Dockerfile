FROM gradle:8.5-jdk21-alpine as builder
WORKDIR /opt/app
COPY . .
RUN ./gradlew shadowjar --no-daemon

FROM amazoncorretto:21.0.2
WORKDIR /opt/app
COPY --from=builder /opt/app/build/libs/app-1.0-SNAPSHOT-all.jar .

ENTRYPOINT ["java","--enable-preview","-jar","app-1.0-SNAPSHOT-all.jar"]