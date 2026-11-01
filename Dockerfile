FROM python:3.12-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN sh build.sh && PYTHONPATH=vendor python package_source.py && PYTHONPATH=vendor python -m unittest discover -q && PYTHONPATH=vendor python package_source.py
FROM python:3.12-slim
WORKDIR /app
COPY --from=build /app /app
RUN useradd --system --uid 10001 appuser
USER appuser
ENV HOST=0.0.0.0 PORT=8080 PYTHONPATH=/app/vendor PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
CMD ["python", "service.py"]
