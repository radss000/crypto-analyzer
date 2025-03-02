# Use a base image with both Node.js and Python
FROM nikolaik/python-nodejs:python3.9-nodejs18

# Set working directory
WORKDIR /app

# Copy package files and install Node dependencies
COPY package*.json ./
RUN npm install

# Copy Python requirements and install Python dependencies
COPY server/python/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Build the React application
RUN npm run build

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application
CMD ["node", "server/index.js"]