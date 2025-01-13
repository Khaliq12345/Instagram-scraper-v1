FROM python:3.12-slim

RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get install libglib2.0-0 -y
RUN apt-get install -y libgomp1

RUN mkdir -p /root/snap/firefox/common/.mozilla/firefox

COPY ./firefox_config /root/snap/firefox/common/.mozilla

WORKDIR /scraperApi

COPY . /scraperApi

RUN pip install -r requirements.txt

RUN playwright install-deps

RUN playwright install

CMD ["python3", "app.py"]