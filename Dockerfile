FROM python:3.5

ADD requirements.txt /requirements.txt
RUN pip install --no-cache-dir --trusted-host mirrors.aliyun.com --index-url http://mirrors.aliyun.com/pypi/simple/ -r /requirements.txt

#ADD . /matelook_mini-facebook
ADD start.sh /start.sh
RUN chmod 755 /start.sh

RUN mkdir -p /matelook_mini-facebook

ENTRYPOINT ["/start.sh"]

# docker build -t munsw .
# docker rm -f munsw; docker run -itd --name=munsw -p 5005:5005 -v /Users/henry/repo/private/matelook_mini-facebook:/matelook_mini-facebook munsw bash
