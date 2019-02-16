FROM python:3.6

WORKDIR /usr/src/app
COPY ./ ./
RUN pip install numpy==1.13.3
RUN pip install Cython==0.29
RUN pip install matplotlib==2.2.2
RUN pip install pylint==2.1.1
RUN pip install -I nose2==0.6.5
RUN pip install -I coverage==4.4.1

RUN pip install -r requirements.txt
