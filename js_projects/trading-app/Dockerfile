FROM node:16

RUN rm -rf node_modules

# Install dependencies
COPY package*.json .
RUN npm install -g npm@9.1.1
RUN npm install

# Copy source files
COPY . .

RUN npm run build
EXPOSE 3000

CMD "npm" "run" "start"