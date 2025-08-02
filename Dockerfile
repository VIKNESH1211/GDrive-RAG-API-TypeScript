# Use Alpine node image
FROM node:22-alpine

# Install necessary OS dependencies for some packages (e.g., pdf-parse)
RUN apk add --no-cache \
    python3 \
    build-base \
    libc6-compat \
    libstdc++ \
    && npm install -g typescript ts-node

# Set working directory
WORKDIR /app

# Copy package files and install deps
COPY package*.json tsconfig.json ./
RUN npm install

# Copy the rest of the app
COPY ./src ./src

EXPOSE 3000
CMD ["npm", "run", "dev"]
