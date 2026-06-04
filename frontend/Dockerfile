# IdeaForge frontend — Vite 8 dev server (Node 22 satisfies Vite 8's engine).
FROM node:22-bookworm-slim

WORKDIR /app

# Install deps first for layer caching. node_modules is kept in a volume at
# runtime (see docker-compose.yml) so the host bind-mount never shadows it.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# --host 0.0.0.0 makes the dev server reachable from the host browser.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
