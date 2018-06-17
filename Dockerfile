FROM python:3.6.5-slim-stretch
LABEL maintainer="operations@wizardsofindustry.net"

# The packages below are generic dependencies for libraries used by
# SG compiled applications.
RUN apt-get update && apt-get install -y libssl-dev libsasl2-2 libsasl2-dev libsasl2-modules
RUN apt-get update && apt-get install -y ssl-cert ca-certificates

# The following commands install the build dependencies, which will be
# removed at a later stage.
RUN apt-get update && apt-get install -y gcc g++ cmake cmake-curses-gui uuid-dev

RUN pip3 install python-qpid-proton==0.21.0
RUN pip3 install pytz==2018.4
RUN pip3 install PyYAML==3.12
RUN pip3 install marshmallow==2.15.0
RUN pip3 install coverage
RUN pip3 install nose

ADD . /usr/local/src/python-aorta
WORKDIR /usr/local/src/python-aorta
RUN ./test
RUN python3.6 setup.py install

# Remove build dependencies.
RUN apt-get autoremove -y gcc g++ cmake cmake-curses-gui uuid-dev --purge
