# Mobile (Ionic + Angular) image: lint + unit tests gate the build, nginx serves the result
# and proxies /api to the API. Build with: docker build -f docker/mobile.Dockerfile .
# Run only the tests:                      docker build -f docker/mobile.Dockerfile --target test .

ARG NODE_VERSION=24

FROM node:${NODE_VERSION}-alpine AS deps
WORKDIR /app
COPY mobile/package.json mobile/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

FROM deps AS test
COPY mobile ./
ENV CI=true NG_CLI_ANALYTICS=false
RUN npm run lint && npm run test:ci

# Built on top of the test stage, so a failing lint or test fails the image build.
FROM test AS build
RUN npm run build -- --configuration production

FROM nginxinc/nginx-unprivileged:1.31-alpine AS runtime
COPY docker/mobile.nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/www /usr/share/nginx/html
# API_URL (http://api:8000 in compose) is substituted into the template at start-up.
ENV API_URL=http://api:8000
EXPOSE 8080
