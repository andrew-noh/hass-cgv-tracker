ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Run the application
CMD ["./run.sh"]

