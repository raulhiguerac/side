FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

EXPOSE 8080

# vue-cli-service escucha en localhost por defecto: sin --host el puerto
# publicado del contenedor no responde.
CMD ["npm", "run", "serve", "--", "--host", "0.0.0.0"]
