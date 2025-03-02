FROM node:18

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY package*.json ./
RUN npm install

COPY server/python/requirements.txt ./server/python/
RUN pip3 install -r server/python/requirements.txt

# Copy application code
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 8000

# Start application
CMD ["node", "server/index.js"]