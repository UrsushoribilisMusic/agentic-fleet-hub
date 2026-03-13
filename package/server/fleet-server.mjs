/**
 * AgentFleet Hub Server
 * Generic fleet management API + static file serving.
 * Drop-in for any multi-agent project.
 *
 * Environment variables:
 *   PORT                   - HTTP port (default: 8787)
 *   FLEET_DATA_DIR         - Path to the data directory (default: ./data)
 *   GOOGLE_CLIENT_ID       - Google OAuth client ID (optional)
 *   GOOGLE_CLIENT_SECRET   - Google OAuth client secret (optional)
 *   GOOGLE_AUTH_COOKIE_SECRET - Cookie signing secret
 *   GOOGLE_AUTH_ALLOWED_EMAILS - Comma-separated list of allowed emails (private fleet)
 *   PUBLIC_URL             - Base URL for OAuth callbacks (default: http://localhost:8787)
 */

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import {
  buildSetupPayload,
  getDefaultFleetMeta,
  getDemoConfig,
  getGrowthConfig,
  getSetupStatus,
  normalizeFleetMeta,
  readJson,
  runDoctor,
  updateBootstrapMetadata,
  writeBootstrapFiles,
  writeJson,
} from "./setup-lib.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PORT = Number(process.env.PORT || 8787);
const PUBLIC_URL = process.env.PUBLIC_URL || `http://localhost:${PORT}`;
const FLEET_DATA_DIR = process.env.FLEET_DATA_DIR || path.join(__dirname, "..", "data");

// Derived data paths
const FLEET_META_PATH  = path.join(FLEET_DATA_DIR, "config", "fleet_meta.json");
const DEMO_META_PATH   = path.join(FLEET_DATA_DIR, "config", "demo_meta.json");
const GROWTH_META_PATH = path.join(FLEET_DATA_DIR, "config", "growth_meta.json");
const LESSONS_PATH     = path.join(FLEET_DATA_DIR, "lessons", "ledger.json");
const INBOX_PATH       = path.join(FLEET_DATA_DIR, "messages", "inbox.json");
const STANDUPS_DIR     = path.join(FLEET_DATA_DIR, "standups");
const STANDUPS_INDEX   = path.join(STANDUPS_DIR, "index.json");

// OAuth (optional — set env vars to enable)
const GOOGLE_CLIENT_ID     = process.env.GOOGLE_CLIENT_ID || "";
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "";
const COOKIE_SECRET        = process.env.GOOGLE_AUTH_COOKIE_SECRET || "change-me-in-production";
const ALLOWED_EMAILS_RAW   = (process.env.GOOGLE_AUTH_ALLOWED_EMAILS || "").split(",").map(e => e.trim().toLowerCase()).filter(Boolean);

// Static roots: map URL prefix → local directory
const STATIC_ROOTS = {
  "/fleet":     path.join(__dirname, "..", "dashboard", "engineering"),
  "/demo":      path.join(__dirname, "..", "dashboard", "demo"),
  "/growth":    path.join(__dirname, "..", "dashboard", "growth"),
  "/setup":     path.join(__dirname, "..", "dashboard", "setup"),
  "/configure": path.join(__dirname, "..", "dashboard", "configure"),
};

// ─── Utilities ───────────────────────────────────────────────────────────────

function now()  { return Date.now(); }
function rid()  { return `req_${now()}_${Math.random().toString(36).slice(2, 8)}`; }

function send(res, code, body, requestId) {
  res.statusCode = code;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  if (requestId) res.setHeader("X-Request-Id", requestId);
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", c => (data += c));
    req.on("end", () => {
      if (!data) return resolve({});
      try { resolve(JSON.parse(data)); } catch { reject(new Error("invalid_json")); }
    });
    req.on("error", reject);
  });
}

function getMimeType(ext) {
  const types = {
    ".html": "text/html; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".mjs":  "application/javascript; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".woff2":"font/woff2",
  };
  return types[ext] || "application/octet-stream";
}

// ─── Cookie helpers (simple HMAC-signed value) ───────────────────────────────

function signCookie(value) {
  const sig = crypto.createHmac("sha256", COOKIE_SECRET).update(value).digest("base64url");
  return `${value}.${sig}`;
}

function verifyCookie(signed) {
  if (!signed) return null;
  const dot = signed.lastIndexOf(".");
  if (dot === -1) return null;
  const value = signed.slice(0, dot);
  const expected = signCookie(value);
  if (!crypto.timingSafeEqual(Buffer.from(signed), Buffer.from(expected))) return null;
  return value;
}

function parseCookies(req) {
  const raw = req.headers.cookie || "";
  return Object.fromEntries(raw.split(";").map(c => c.trim().split("=").map(decodeURIComponent)));
}

function getAuthedEmail(req) {
  const cookies = parseCookies(req);
  return verifyCookie(cookies["fleet_auth"] || "");
}

// ─── OAuth flow (optional) ───────────────────────────────────────────────────

const oauthStates = new Map(); // state → { next, expires }

function buildOAuthUrl(state) {
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: `${PUBLIC_URL}/auth/callback`,
    response_type: "code",
    scope: "openid email profile",
    state,
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
}

async function exchangeCode(code) {
  const params = new URLSearchParams({
    code,
    client_id: GOOGLE_CLIENT_ID,
    client_secret: GOOGLE_CLIENT_SECRET,
    redirect_uri: `${PUBLIC_URL}/auth/callback`,
    grant_type: "authorization_code",
  });
  const res = await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: params });
  if (!res.ok) throw new Error("token_exchange_failed");
  const data = await res.json();
  const [, payloadB64] = data.id_token.split(".");
  const payload = JSON.parse(Buffer.from(payloadB64, "base64url").toString());
  return payload.email?.toLowerCase() || null;
}

// ─── Static file serving ─────────────────────────────────────────────────────

function serveStatic(urlPath, res) {
  let matched = null;
  let localPath = null;

  for (const [prefix, root] of Object.entries(STATIC_ROOTS)) {
    if (urlPath === prefix || urlPath.startsWith(prefix + "/")) {
      matched = prefix;
      const relative = urlPath.slice(prefix.length) || "/index.html";
      localPath = path.join(root, relative === "/" ? "index.html" : relative);
      break;
    }
  }

  if (!matched) return false;

  // Enforce trailing slash redirect
  if (urlPath === matched) {
    res.statusCode = 301;
    res.setHeader("Location", matched + "/");
    res.end();
    return true;
  }

  if (!localPath || !fs.existsSync(localPath)) {
    // Try index.html for directory requests
    const asDir = path.join(localPath, "index.html");
    if (fs.existsSync(asDir)) {
      localPath = asDir;
    } else {
      res.statusCode = 404;
      res.end("Not found");
      return true;
    }
  }

  const ext = path.extname(localPath);
  res.setHeader("Content-Type", getMimeType(ext));
  res.setHeader("Cache-Control", ext === ".html" ? "no-cache" : "public, max-age=3600");
  res.statusCode = 200;
  fs.createReadStream(localPath).pipe(res);
  return true;
}

// ─── Request handler ─────────────────────────────────────────────────────────

async function handler(req, res) {
  const requestId = rid();
  res.setHeader("X-Request-Id", requestId);

  const url = new URL(req.url, `http://localhost`);
  const urlPath = url.pathname;
  const fleetMeta = normalizeFleetMeta(readJson(FLEET_META_PATH, getDefaultFleetMeta()));
  const setupCompleted = fleetMeta.meta.installation.setup_completed;

  // ── Health check ────────────────────────────────────────────────────────
  if (urlPath === "/health") {
    return send(res, 200, { ok: true, ts: now() }, requestId);
  }

  // ── OAuth endpoints (only if Google OAuth is configured) ─────────────────
  if (GOOGLE_CLIENT_ID && GOOGLE_CLIENT_SECRET) {
    if (urlPath === "/auth/login") {
      const state = crypto.randomBytes(16).toString("hex");
      const next = url.searchParams.get("next") || "/fleet/";
      oauthStates.set(state, { next, expires: now() + 5 * 60 * 1000 });
      res.statusCode = 302;
      res.setHeader("Location", buildOAuthUrl(state));
      return res.end();
    }

    if (urlPath === "/auth/callback") {
      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      const stateData = oauthStates.get(state);
      if (!code || !stateData || stateData.expires < now()) {
        return send(res, 400, { ok: false, error: "invalid_state" }, requestId);
      }
      oauthStates.delete(state);
      try {
        const email = await exchangeCode(code);
        if (!email || (ALLOWED_EMAILS_RAW.length && !ALLOWED_EMAILS_RAW.includes(email))) {
          return send(res, 403, { ok: false, error: "not_allowed" }, requestId);
        }
        const cookie = signCookie(email);
        res.setHeader("Set-Cookie", `fleet_auth=${encodeURIComponent(cookie)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400`);
        res.statusCode = 302;
        res.setHeader("Location", stateData.next);
        return res.end();
      } catch (e) {
        return send(res, 500, { ok: false, error: e.message }, requestId);
      }
    }

    if (urlPath === "/auth/logout") {
      res.setHeader("Set-Cookie", "fleet_auth=; Path=/; Max-Age=0");
      res.statusCode = 302;
      res.setHeader("Location", "/demo/");
      return res.end();
    }
  }

  // ── Fleet API ─────────────────────────────────────────────────────────────
  if (urlPath.startsWith("/fleet/api/")) {
    // Auth gate for private fleet API (skip for /demo and /growth)
    if (GOOGLE_CLIENT_ID && GOOGLE_CLIENT_SECRET) {
      const email = getAuthedEmail(req);
      if (!email) {
        return send(res, 401, { ok: false, error: "unauthenticated" }, requestId);
      }
    }

    // GET /fleet/api/config — full fleet config
    if (urlPath === "/fleet/api/config" && req.method === "GET") {
      return send(res, 200, fleetMeta, requestId);
    }

    // POST /fleet/api/config — overwrite full fleet config
    if (urlPath === "/fleet/api/config" && req.method === "POST") {
      const body = await readBody(req);
      const normalized = normalizeFleetMeta(body);
      writeJson(FLEET_META_PATH, normalized);
      return send(res, 200, { ok: true, config: normalized }, requestId);
    }

    // GET /fleet/api/config/demo — public demo config
    if (urlPath === "/fleet/api/config/demo" && req.method === "GET") {
      return send(res, 200, getDemoConfig(fleetMeta, readJson(DEMO_META_PATH, { team: [], projects: [] })), requestId);
    }

    // GET /fleet/api/config/growth — growth template config
    if (urlPath === "/fleet/api/config/growth" && req.method === "GET") {
      return send(res, 200, getGrowthConfig(fleetMeta, readJson(GROWTH_META_PATH, { team: [], projects: [] })), requestId);
    }

    // GET /fleet/api/setup/status
    if (urlPath === "/fleet/api/setup/status" && req.method === "GET") {
      return send(res, 200, getSetupStatus(fleetMeta), requestId);
    }

    // GET /fleet/api/setup/doctor
    if (urlPath === "/fleet/api/setup/doctor" && req.method === "GET") {
      return send(res, 200, runDoctor(fleetMeta), requestId);
    }

    // POST /fleet/api/setup
    if (urlPath === "/fleet/api/setup" && req.method === "POST") {
      const body = await readBody(req);
      let nextMeta = buildSetupPayload(fleetMeta, body);
      let bootstrap = null;

      if (body.write_to_repo === true) {
        bootstrap = writeBootstrapFiles(nextMeta, body.repo_path);
        nextMeta = updateBootstrapMetadata(nextMeta, bootstrap);
      }

      writeJson(FLEET_META_PATH, nextMeta);
      return send(
        res,
        200,
        {
          ok: true,
          setup: getSetupStatus(nextMeta),
          bootstrap,
        },
        requestId
      );
    }

    // GET /fleet/api/lessons
    if (urlPath === "/fleet/api/lessons" && req.method === "GET") {
      return send(res, 200, readJson(LESSONS_PATH, []), requestId);
    }

    // POST /fleet/api/lessons
    if (urlPath === "/fleet/api/lessons" && req.method === "POST") {
      const body = await readBody(req);
      const ledger = readJson(LESSONS_PATH, []);
      const lesson = {
        id:         body.id || `lesson-${now()}`,
        title:      body.title || "Untitled Lesson",
        category:   body.category || "general",
        project:    body.project || "Fleet",
        symptom:    body.symptom || "",
        root_cause: body.root_cause || "",
        lesson:     body.lesson || "",
        agent:      body.agent || "Unknown",
        date:       new Date().toISOString(),
        status:     "pending_review",
      };
      ledger.unshift(lesson);
      writeJson(LESSONS_PATH, ledger);
      return send(res, 201, { ok: true, lesson }, requestId);
    }

    // PATCH /fleet/api/lessons/:id
    const lessonPatch = urlPath.match(/^\/fleet\/api\/lessons\/([^/]+)$/);
    if (lessonPatch && req.method === "PATCH") {
      const id = lessonPatch[1];
      const body = await readBody(req);
      const ledger = readJson(LESSONS_PATH, []);
      const idx = ledger.findIndex(l => l.id === id);
      if (idx === -1) return send(res, 404, { ok: false, error: "lesson_not_found" }, requestId);
      ledger[idx] = { ...ledger[idx], ...body };
      writeJson(LESSONS_PATH, ledger);
      return send(res, 200, { ok: true, lesson: ledger[idx] }, requestId);
    }

    // GET /fleet/api/messages
    if (urlPath === "/fleet/api/messages" && req.method === "GET") {
      return send(res, 200, readJson(INBOX_PATH, []), requestId);
    }

    // POST /fleet/api/messages
    if (urlPath === "/fleet/api/messages" && req.method === "POST") {
      const body = await readBody(req);
      const inbox = readJson(INBOX_PATH, []);
      const msg = {
        id:         `msg-${now()}`,
        timestamp:  new Date().toISOString(),
        from:       body.from || "Unknown",
        to:         body.to || "All",
        subject:    body.subject || "(no subject)",
        body:       body.body || "",
        status:     "unread",
        priority:   body.priority || "normal",
        ref_ticket: body.ref_ticket || null,
      };
      inbox.unshift(msg);
      writeJson(INBOX_PATH, inbox);
      return send(res, 201, { ok: true, message: msg }, requestId);
    }

    // PATCH /fleet/api/messages/:id
    const msgPatch = urlPath.match(/^\/fleet\/api\/messages\/([^/]+)$/);
    if (msgPatch && req.method === "PATCH") {
      const id = msgPatch[1];
      const body = await readBody(req);
      const inbox = readJson(INBOX_PATH, []);
      const idx = inbox.findIndex(m => m.id === id);
      if (idx === -1) return send(res, 404, { ok: false, error: "message_not_found" }, requestId);
      inbox[idx] = { ...inbox[idx], ...body };
      writeJson(INBOX_PATH, inbox);
      return send(res, 200, { ok: true, message: inbox[idx] }, requestId);
    }

    // POST /fleet/api/standup
    if (urlPath === "/fleet/api/standup" && req.method === "POST") {
      const body = await readBody(req);
      const date = body.date || new Date().toISOString().slice(0, 10);
      fs.mkdirSync(STANDUPS_DIR, { recursive: true });
      const filePath = path.join(STANDUPS_DIR, `${date}.md`);
      const entry = `\n## ${body.agent || "Unknown"}\n\n- Done: ${body.done || "(none)"}\n- Today: ${body.today || "(none)"}\n- Blockers: ${body.blockers || "None"}\n`;
      fs.appendFileSync(filePath, entry);
      // Update index
      const index = readJson(STANDUPS_INDEX, []);
      if (!index.find(i => i.date === date)) {
        index.unshift({ date, file: `${date}.md`, summary: body.summary || entry.slice(0, 80) });
        writeJson(STANDUPS_INDEX, index);
      }
      return send(res, 200, { ok: true }, requestId);
    }

    return send(res, 404, { ok: false, error: "not_found" }, requestId);
  }

  // ── Static file serving ───────────────────────────────────────────────────
  if (serveStatic(urlPath, res)) return;

  // ── Root redirect ─────────────────────────────────────────────────────────
  if (urlPath === "/" || urlPath === "") {
    res.statusCode = 302;
    res.setHeader("Location", setupCompleted ? "/demo/" : "/setup/");
    return res.end();
  }

  if ((urlPath === "/fleet" || urlPath === "/fleet/") && !setupCompleted) {
    res.statusCode = 302;
    res.setHeader("Location", "/setup/");
    return res.end();
  }

  send(res, 404, { ok: false, error: "not_found" }, requestId);
}

// ─── Start ────────────────────────────────────────────────────────────────────

const server = http.createServer(async (req, res) => {
  try {
    await handler(req, res);
  } catch (err) {
    console.error("[fleet-server] unhandled error:", err.message);
    if (!res.headersSent) {
      res.statusCode = 500;
      res.end(JSON.stringify({ ok: false, error: "internal_error" }));
    }
  }
});

server.listen(PORT, () => {
  console.log(`[fleet-server] Running on http://localhost:${PORT}`);
  console.log(`[fleet-server] Data dir: ${FLEET_DATA_DIR}`);
  console.log(`[fleet-server] OAuth: ${GOOGLE_CLIENT_ID ? "enabled" : "disabled (set GOOGLE_CLIENT_ID to enable)"}`);
});
