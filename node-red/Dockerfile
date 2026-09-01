# Image με τις βιβλιοθήκες του flow.
FROM nodered/node-red:4.1.13-20

COPY --chown=node-red:node-red package.json package-lock.json /data/
RUN cd /data && npm ci --omit=dev --no-audit --no-fund

COPY --chown=node-red:node-red settings.js /data/settings.js
COPY --chown=node-red:node-red flows.json /data/flows.json
