FROM python:3.11-slim

WORKDIR /app

# Copy package files
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Install package
RUN pip install --no-cache-dir .

# Default port (Fly.io sets PORT env var)
ENV PORT=8080
EXPOSE 8080

# Run HTTP server
CMD ["pinescript-mcp", "--http"]
