FROM node:20-alpine

ARG EINSTORE_GIT_REF=main

RUN apk add --no-cache git

RUN git clone --depth 1 --recurse-submodules --branch "${EINSTORE_GIT_REF}" https://github.com/Einstore/Einstore.git /app

WORKDIR /app/Admin

RUN npm install

EXPOSE 8101

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8101"]
