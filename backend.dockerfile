FROM python:3.12-slim-bullseye

LABEL maintainer="Jonathan Bereyziat <jonathan@be-dev.ch>"

ARG TAG
RUN echo "Building Docker image with TAG: ${TAG}"

COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh

COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh

COPY ./gunicorn_conf.py /gunicorn_conf.py

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.7.7 /uv /bin/uv

# Set up Python environment
ENV PYTHONPATH=/app
# Set the working directory
WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./
RUN bash -c "if [ $TAG == 'dev' ]; then uv export --no-hashes > requirements.txt; else uv export --no-hashes --no-dev > requirements.txt; fi"
RUN uv pip install --system -r requirements.txt

COPY . /app

EXPOSE 80

CMD ["/start.sh"]