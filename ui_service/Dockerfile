# Stage 1: Build React Frontend
FROM node:20-slim AS build-frontend
WORKDIR /app/client
COPY client/package*.json ./
RUN npm install
COPY client/ ./
RUN npm run build

# Stage 2: Build Node.js Backend & Run
FROM node:20-slim
WORKDIR /app

# Copy server files
COPY server/package*.json ./server/
RUN cd server && npm install

COPY server/ ./server/

# Copy frontend build from stage 1
COPY --from=build-frontend /app/client/dist ./client/dist

EXPOSE 3000

ENV PORT=3000
CMD ["node", "server/index.js"]
