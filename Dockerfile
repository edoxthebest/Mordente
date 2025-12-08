FROM python:3.13 AS libmata
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

RUN pip install -e .


FROM mordente
WORKDIR /usr/local/payload-dumper

RUN wget -q https://github.com/ssut/payload-dumper-go/releases/download/1.3.0/payload-dumper-go_1.3.0_linux_amd64.tar.gz
RUN tar -xvzf payload-dumper-go_1.3.0_linux_amd64.tar.gz
RUN chmod +x payload-dumper-go
RUN mv payload-dumper-go /usr/local/bin

WORKDIR /usr/local/Mordente