# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
CMD sh -c "mkdir -p result_build/build && cp -r build/. result_build/build/"
