FROM --platform=$BUILDPLATFORM python:3.13 AS libmata
WORKDIR /usr/local/mata

COPY mata .

RUN apt-get update && apt-get install -y cmake
RUN make -C bindings/python init build-dist
RUN pip install bindings/python/dist/libmata-1.20.0.tar.gz


FROM libmata AS setools
WORKDIR /usr/local/setools

COPY setools .
COPY selinux ./selinux

RUN apt-get update && apt-get install -y flex
RUN cd selinux/libsepol && make install 
RUN SEPOL_SRC=selinux/libsepol/ python setup.py build_ext
RUN pip install . 


FROM setools AS mordente
WORKDIR /usr/local/Mordente

COPY pyproject.toml ./
COPY src ./src
COPY policies ./policies
COPY queries ./queries
COPY SEAExtract ./

RUN pip install -e .


FROM mordente
WORKDIR /usr/local/payload-dumper

ARG TARGETARCH
COPY "payload-dumper-go_1.3.0_linux_${TARGETARCH}.tar.gz" .
RUN tar -xvzf "payload-dumper-go_1.3.0_linux_${TARGETARCH}.tar.gz"
RUN chmod +x payload-dumper-go
RUN mv payload-dumper-go /usr/local/bin

RUN apt-get update && apt-get install -y p7zip erofs-utils

WORKDIR /usr/local/Mordente