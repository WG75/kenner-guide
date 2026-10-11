import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { canSave, normalisePlan, SAVE_BLOCKED_MESSAGE } from "../lib/members-plan.js";
import { buildChecklist, validateItem, validateListName } from "../lib/collection-model.js";
import { getStore } from "../lib/collection-store.js";
import {
  membersMode,
  publicConfig,
  signDevSession,
  devCookie,
  readMember
} from "../lib/members-auth.js";

function loadFigures() {
  const here = path.dirname(fileURLToPath(import.meta.url));
  const candidates = [
    path.join(process.cwd(), "data", "kenner-debut-figures.json"),
    path.join(here, "..", "data", "kenner-debut-figures.json")
  ];
  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(fs.readFileSync(candidate, "utf8"));
      return Array.isArray(parsed.figures) ? parsed.figures : [];
    } catch (err) {
      // Try the next location.
    }
  }
  return [];
}

function send(res, status, body, headers) {
  if (headers) {
    for (const [key, value] of Object.entries(headers)) res.setHeader(key, value);
  }
  return res.status(status).json(body);
}

function actionOf(req) {
  const url = new URL(req.url || "/api/members", "http://localhost");
  const fromQuery = url.searchParams.get("action");
  if (fromQuery) return fromQuery;
  const body = req.body || {};
  return typeof body.action === "string" ? body.action : "";
}

async function signedIn(req) {
  try {
    return await readMember(req);
  } catch (err) {
    console.error("Member sign-in check failed:", err && err.message);
    return null;
  }
}

export default async function handler(req, res) {
  const action = actionOf(req);
  if (req.method === "GET" && !action) {
    return send(res, 200, publicConfig());
  }
  if (action === "config") return send(res, 200, publicConfig());

  const mode = membersMode();
  if (mode === "off") {
    return send(res, 404, { error: "members_off", message: "Member accounts are not switched on." });
  }

  if (action === "dev-sign-in") {
    if (mode !== "dev") return send(res, 404, { error: "members_off", message: "Member accounts are not switched on." });
    const email = String((req.body || {}).email || "").trim().toLowerCase();
    const provider = (req.body || {}).provider;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return send(res, 400, { error: "bad_email", message: "Enter an email address to sign in on this computer." });
    }
    const token = signDevSession(email, provider);
    return send(res, 200, { signedIn: true }, { "Set-Cookie": devCookie(token) });
  }

  if (action === "dev-sign-out") {
    if (mode !== "dev") return send(res, 404, { error: "members_off" });
    return send(res, 200, { signedIn: false }, { "Set-Cookie": devCookie("") });
  }

  const session = await signedIn(req);
  if (!session) {
    if (action === "me") return send(res, 200, { signedIn: false });
    return send(res, 401, { error: "signed_out", message: "Sign in to save a figure." });
  }

  const store = getStore();
  const member = await store.ensureMember({
    id: session.id,
    email: session.email,
    plan: normalisePlan(session.plan)
  });
  const plan = member.plan || session.plan;
  const allowed = canSave(plan);

  if (action === "me") {
    return send(res, 200, {
      signedIn: true,
      member: { id: member.id, email: member.email, plan, canSave: allowed }
    });
  }

  if (!allowed && ["save-item", "update-item", "move-item", "create-list", "rename-list"].includes(action)) {
    return send(res, 403, { error: "plan_blocked", message: SAVE_BLOCKED_MESSAGE });
  }

  const body = req.body || {};

  if (action === "lists") return send(res, 200, { lists: await store.listsFor(member.id) });

  if (action === "create-list") {
    const name = validateListName(body.name);
    if (!name.ok) return send(res, 400, name);
    const created = await store.createList(member.id, name.name);
    if (created.error) return send(res, 400, created);
    return send(res, 200, created);
  }

  if (action === "rename-list") {
    const name = validateListName(body.name);
    if (!name.ok) return send(res, 400, name);
    const renamed = await store.renameList(member.id, body.listId, name.name);
    if (renamed.error) return send(res, 400, renamed);
    return send(res, 200, renamed);
  }

  if (action === "delete-list") {
    const removed = await store.deleteList(member.id, body.listId);
    if (removed.error) return send(res, 400, removed);
    return send(res, 200, removed);
  }

  if (action === "items") {
    return send(res, 200, await store.itemsFor(member.id, body.listId));
  }

  if (action === "save-item" || action === "update-item") {
    const validated = validateItem(body);
    if (!validated.ok) return send(res, 400, validated);
    const saved = action === "save-item"
      ? await store.saveItem(member.id, body.listId, validated.item)
      : await store.updateItem(member.id, body.itemId, validated.item);
    if (saved.error) return send(res, 400, saved);
    return send(res, 200, saved);
  }

  if (action === "move-item") {
    const moved = await store.moveItem(member.id, body.itemId, body.listId);
    if (moved.error) return send(res, 400, moved);
    return send(res, 200, moved);
  }

  if (action === "delete-item") {
    const removed = await store.deleteItem(member.id, body.itemId);
    if (removed.error) return send(res, 400, removed);
    return send(res, 200, removed);
  }

  if (action === "checklist") {
    const items = await store.allItems(member.id);
    return send(res, 200, buildChecklist(loadFigures(), items));
  }

  return send(res, 400, { error: "unknown_action", message: "That member action is not recognised." });
}
