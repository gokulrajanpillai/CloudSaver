FROM python:3.12.11-bullseye

# Set working directory
WORKDIR /workspace

# Copy requirements.txt from local context to container
COPY requirements.txt .

# Install Python dependencies and pre-commit
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
