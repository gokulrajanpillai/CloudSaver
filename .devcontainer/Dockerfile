FROM python:3.12.11-bullseye

# Set working directory
WORKDIR /workspace

# Copy requirements.txt from local context to container
COPY requirements.txt .

# Install Python dependencies and pre-commit
RUN pip install uv==0.8.8 && \
    uv tool install pre-commit==4.2.0 && \
    uv pip install --system -r requirements.txt

# Add uv tools to PATH
ENV PATH="/root/.local/bin:${PATH}"
