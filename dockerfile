FROM node:18

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app

# Copy package files and install Node dependencies
COPY package*.json ./
RUN npm install

# Copy Python requirements and install Python dependencies
COPY server/python/requirements.txt ./
RUN pip3 install -r requirements.txt

# Copy the rest of the application
COPY . .

# Build the frontend
RUN npm run build

# Expose the port
EXPOSE 8000

# Start the application
CMD ["npm", "start"]