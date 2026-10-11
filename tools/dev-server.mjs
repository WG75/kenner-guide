/* Local site for member features. Sets test mode and keeps collections in a
   file on this computer. It does not call Clerk or Neon. */
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
process.chdir(root);
process.env.MEMBERS_DEV = "1";
if (process.env.MEMBERS_USE_DATABASE !== "1") delete process.env.DATABASE_URL;
process.env.MEMBERS_STORE_PATH = process.env.MEMBERS_STORE_PATH || path.join(os.tmpdir(), "sw7885-members.json");

const chat = (await import(pathToFileURL(path.join(root, "api", "chat.js")).href)).default;
const members = (await import(pathToFileURL(path.join(root, "api", "members.js")).href)).default;

const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".txt": "text/plain; charset=utf-8"
};

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

const port = Number(process.env.PORT) || 4173;
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url || "/", "http://localhost");
  if (url.pathname === "/api/chat" || url.pathname === "/api/members") {
    const raw = await readBody(req);
    let body = {};
    if (raw) {
      try {
        body = JSON.parse(raw);
      } catch (err) {
        res.writeHead(400, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: "bad_json", message: "That request could not be read." }));
        return;
      }
    }
    const headers = {};
    const handler = url.pathname === "/api/chat" ? chat : members;
    const vercelRes = {
      statusCode: 200,
      setHeader(key, value) { headers[key.toLowerCase()] = value; },
      status(code) { this.statusCode = code; return this; },
      json(obj) {
        res.writeHead(this.statusCode, { "content-type": "application/json; charset=utf-8", ...headers });
        res.end(JSON.stringify(obj));
      }
    };
    try {
      await handler({ method: req.method, url: req.url, headers: req.headers, body }, vercelRes);
    } catch (err) {
      console.error(err);
      if (!res.headersSent) {
        res.writeHead(500, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: "server_error", message: "Something went wrong." }));
      }
    }
    return;
  }

  const requested = decodeURIComponent(url.pathname);
  const relative = (requested === "/" ? "index.html" : requested).replace(/^\/+/, "");
  const filePath = path.resolve(root, relative);
  if (filePath !== root && !filePath.startsWith(root + path.sep)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    res.writeHead(200, { "content-type": types[path.extname(filePath)] || "application/octet-stream" });
    res.end(data);
  });
});

server.listen(port, "0.0.0.0", () => {
  console.log(`SW-7885 local site http://127.0.0.1:${port}`);
});
