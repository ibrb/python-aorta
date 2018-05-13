FROM python:3.6.4-stretch
LABEL maintainer="operations@ibrb.org"

RUN pip3 install python-qpid-proton==0.20.0
RUN pip3 install pytz==2018.3
RUN pip3 install PyYAML==3.12
RUN pip3 install marshmallow==2.15.0
RUN pip3 install coverage
RUN pip3 install nose

ADD . /usr/local/src/python-aorta
WORKDIR /usr/local/src/python-aorta
#RUN ./test
RUN python3.6 setup.py install
