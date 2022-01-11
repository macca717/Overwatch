FROM python:3.9
# ARG var_build
# ENV BUILD_ID=$var_build
RUN apt-get install -y --no-install-recommends libglib2.0; rm -rf /var/lib/apt/lists/*
EXPOSE 9001
EXPOSE 9876
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
ENV LOG_LEVEL "error"
RUN mkdir /saves
COPY alembic.ini alembic.ini
COPY ./migrations ./migrations
COPY ./app /app/
CMD python -O -m app -c config.toml --log-level ${LOG_LEVEL}
