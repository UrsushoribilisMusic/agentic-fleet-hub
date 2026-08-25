'use strict';

const express = require('express');
const { migrate } = require('./db/migrate');
const { buildRouter } = require('./api/router');

const PORT = parseInt(process.env.CANIS_PORT || '4200', 10);

const app = express();
app.use(express.json({ limit: '30mb' }));

const db = migrate();
const router = buildRouter(db);

app.use('/api', router);
app.use('/', router);

app.get('/health', (_req, res) => res.json({ ok: true, service: 'canis-backend' }));

if (require.main === module) {
  app.listen(PORT, () => {
    console.log('[canis-server] listening on port', PORT);
  });
}

module.exports = { app, db };
