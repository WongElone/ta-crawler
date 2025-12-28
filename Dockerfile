FROM python:3.12

# Set working directory
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy only the dependency files to leverage Docker cache
COPY pyproject.toml uv.lock /app/

# Install project dependencies using uv
# --no-dev skips development dependencies
# --locked ensures we use exact versions from uv.lock
RUN uv sync --no-dev --locked

# Copy the application code
COPY . /app/crawler

# Create log directory
RUN mkdir -p /logs/crawler

# Copy the run scripts and make them executable
COPY start.sh .
RUN chmod +x start.sh

COPY stop.sh .
RUN chmod +x stop.sh

# Command to run the application
ENTRYPOINT ["./start.sh"]
