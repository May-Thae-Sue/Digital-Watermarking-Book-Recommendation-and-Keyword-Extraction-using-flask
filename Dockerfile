FROM python:3.7
WORKDIR /
# RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
# RUN apk add --no-cache gcc musl-dev linux-headers
# RUN apk --upgrade --no-cache add gfortran build-base wget freetype-dev libpng-dev openblas-dev libxml2-dev libxslt-dev
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader -d ./nltk_data all
# RUN apk update && apk add bash
COPY . .
ENV FLASK_APP /app.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_DEBUG=1
ENV FLASK_ENV=development
CMD ["flask", "run"]
