FROM alpine:3.20 AS builder

WORKDIR /app

RUN apk update && apk add --no-cache build-base git cmake bash make linux-headers
RUN git clone https://github.com/gpac/gpac.git gpac-master

WORKDIR /app/gpac-master

RUN ./configure --static-bin --use-zlib=no --prefix=/usr/bin
RUN make -j$(nproc)

WORKDIR /app

RUN git clone --branch 5.10.6 https://github.com/cyr-ius/userland.git userland

WORKDIR /app/userland
RUN sed -i 's/sudo//g' buildme
RUN /bin/bash -c ./buildme


# ------------- Builder python ---------------
FROM python:3.12-alpine AS python-builder

WORKDIR /app

# Venv python
RUN python3 -m venv --system-site-packages --upgrade-deps /env
ENV VIRTUAL_ENV=/env
ENV PATH=$PATH:/env/bin

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Add binaries and sources
ADD requirements.txt requirements.txt

# Install dependencies
RUN apk add --no-cache --virtual build build-base python3-dev cmake make gcc linux-headers ninja git rust cargo libressl-dev libffi-dev
RUN /env/bin/pip3 install --upgrade pip wheel
RUN /env/bin/pip3 install -v --no-cache-dir -r requirements.txt

# ------------- MAIN ---------------
FROM python:3.12-alpine3.20

# Add binaries
COPY --from=builder /app/gpac-master/bin/gcc/MP4Box /usr/bin
COPY --from=builder /app/gpac-master/bin/gcc/gpac /usr/bin
COPY --from=builder /app/userland/build/bin /usr/bin
COPY --from=builder /app/userland/build/lib /usr/lib

# set version label
LABEL org.opencontainers.image.source="https://github.com/cyr-ius/viewpicam"
LABEL org.opencontainers.image.description="Backend Viewpicam - inspired by Rpi Cam Interface"
LABEL org.opencontainers.image.licenses="MIT"
LABEL maintaine="cyr-ius"

# Venv python
RUN python3 -m venv --system-site-packages --upgrade-deps /env
ENV VIRTUAL_ENV=/env
ENV PATH=$PATH:/env/bin

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container loggi.................. ng
ENV PYTHONUNBUFFERED=1

# Enable VirtualEnv
ENV VIRTUAL_ENV="/env"
ENV PATH="/env/bin:$PATH"

WORKDIR /app

COPY --from=python-builder /env /env
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY ./app /app/app
COPY ./macros /app/macros
COPY raspimjpeg /etc/raspimjpeg
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod 744 /etc/raspimjpeg
RUN chmod 744 -R /app/macros
RUN chmod 744 -R /docker-entrypoint.sh

# VOLUME /app/static
VOLUME /app/macros
VOLUME /app/data
VOLUME /app/h264
VOLUME /app/config

ARG VERSION
ENV VERSION=${VERSION}

EXPOSE 8000/tcp
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
