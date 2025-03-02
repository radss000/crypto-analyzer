FROM node:18-slim

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node dependencies
RUN npm install

# Copy Python requirements and install Python dependencies
COPY server/python/requirements.txt ./server/python/
RUN pip3 install -r server/python/requirements.txt

# Copy the rest of the application
COPY . .

# Build the frontend
RUN npm run build

# Expose the port
EXPOSE 8000

# Start the application
CMD ["node", "server/index.js"]