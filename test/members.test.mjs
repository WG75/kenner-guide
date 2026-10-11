// Gating and the collection data model. No Clerk, Neon, or network.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { GRADES } from "../lib/condition-grades.js";
import { canSave, SAVE_BLOCKED_MESSAGE } from "../lib/members-plan.js";
import { applyIdentification, buildChecklist, identificationReady, validateItem } from "../lib/collection-model.js";
import { createFileStore, resetStoreForTests } from "../lib/collection-store.js";
import { membersMode, publicConfig } from "../lib/members-auth.js";
import { saveActionVisible } from "../members-ui.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const envKeys = ["DATABASE_URL", "MEMBERS_DEV", "MEMBERS_DEV_PLAN", "MEMBERS_STORE_PATH", "MEMBERS_DEV_SECRET", "CLERK_SECRET_KEY", "CLERK_PUBLISHABLE_KEY", "VERCEL_ENV"];
const savedEnv = Object.fromEntries(envKeys.map(key => [key, process.env[key]]));
for (const key of envKeys) delete process.env[key];

const { default: handler } = await import("../api/members.js");

function restoreEnv() {
  for (const key of envKeys) {
    if (savedEnv[key] === undefined) delete process.env[key];
    else process.env[key] = savedEnv[key];
  }
}

function mockRes() {
  return {
    statusCode: 0,
    body: null,
    headers: {},
    setHeader(key, value) { this.headers[key.toLowerCase()] = value; },
    status(code) { this.statusCode = code; return this; },
    json(obj) { this.body = obj; return this; }
  };
}

async function call(body, headers = {}) {
  const res = mockRes();
  await handler({ method: "POST", url: "/api/members", headers, body }, res);
  return res;
}

let passed = 0;
let failed = 0;
async function test(name, fn) {
  resetStoreForTests();
  for (const key of envKeys) delete process.env[key];
  try {
    await fn();
    passed += 1;
    console.log(`ok ${name}`);
  } catch (err) {
    failed += 1;
    console.error(`not ok ${name}`);
    console.error(err);
  }
}

await test("members stay hidden when Clerk is not configured", async () => {
  assert.equal(membersMode(), "off");
  assert.deepEqual(publicConfig(), { enabled: false, mode: "off", providers: [] });
  const res = mockRes();
  await handler({ method: "GET", url: "/api/members", headers: {}, body: {} }, res);
  assert.equal(res.statusCode, 200);
  assert.equal(res.body.enabled, false);
  const save = await call({ action: "save-item", figureName: "Jawa" });
  assert.equal(save.statusCode, 404);
});

await test("local dev mode is ignored on a production deployment", () => {
  process.env.MEMBERS_DEV = "1";
  process.env.VERCEL_ENV = "production";
  assert.equal(membersMode(), "off");
  process.env.CLERK_PUBLISHABLE_KEY = "pk_test_example";
  process.env.CLERK_SECRET_KEY = "sk_test_example";
  assert.equal(membersMode(), "clerk");
  const config = publicConfig();
  assert.deepEqual(config.providers, ["email", "google", "facebook"]);
  assert.equal(config.publishableKey, "pk_test_example");
});

await test("a signed-out visitor cannot save, and a dev session can", async () => {
  process.env.MEMBERS_DEV = "1";
  const denied = await call({ action: "me" });
  assert.equal(denied.statusCode, 200);
  assert.equal(denied.body.signedIn, false);
  const blocked = await call({ action: "save-item", figureName: "Jawa" });
  assert.equal(blocked.statusCode, 401);
  const signIn = await call({ action: "dev-sign-in", email: "collector@example.com", provider: "google" });
  assert.equal(signIn.statusCode, 200);
  const cookie = signIn.headers["set-cookie"].split(";")[0];
  const me = await call({ action: "me" }, { cookie });
  assert.equal(me.body.member.email, "collector@example.com");
  assert.equal(me.body.member.canSave, true);
  assert.equal(me.body.member.plan, "free");
  const bad = await call({ action: "dev-sign-in", email: "not-an-email", provider: "facebook" });
  assert.equal(bad.statusCode, 400);
});

await test("Mint is rejected and Near Mint is the top grade", async () => {
  assert.equal(GRADES[0], "Near Mint");
  assert.equal(GRADES.some(grade => grade.toLowerCase() === "mint"), false);
  assert.equal(validateItem({ figureName: "Jawa", figureGrade: "Mint" }).error, "mint_not_a_grade");
  assert.equal(validateItem({ figureName: "Jawa", accessories: [{ name: "blaster", grade: "Mint" }] }).error, "mint_not_a_grade");
  const saved = validateItem({
    figureName: "Luke Skywalker",
    factory: "Unitoy",
    mould: "F1",
    coo: "Hong Kong",
    figureGrade: "near mint",
    ownedOn: "2026-10-11",
    accessories: [{ name: "lightsaber", variant: "double telescoping", grade: "Fine" }]
  });
  assert.equal(saved.ok, true);
  assert.equal(saved.item.figureGrade, "Near Mint");
  assert.equal(saved.item.accessories[0].grade, "Fine");
  assert.equal(saved.item.ownedOn, "2026-10-11");
});

await test("a lapsed plan cannot save, and a free member can", () => {
  assert.equal(canSave("free"), true);
  assert.equal(canSave("member"), true);
  assert.equal(canSave("subscriber"), true);
  assert.equal(canSave("lapsed"), false);
  assert.match(SAVE_BLOCKED_MESSAGE, /not included/);
});

await test("lists, grades, move, delete and the checklist", async () => {
  process.env.MEMBERS_DEV = "1";
  const signIn = await call({ action: "dev-sign-in", email: "owner@example.com", provider: "email" });
  const cookie = signIn.headers["set-cookie"].split(";")[0];
  const headers = { cookie };
  const lists = await call({ action: "lists" }, headers);
  assert.equal(lists.body.lists[0].name, "Personal Collection");
  assert.equal(lists.body.lists[0].isDefault, true);
  const kept = await call({ action: "delete-list", listId: lists.body.lists[0].id }, headers);
  assert.equal(kept.body.error, "default_list");
  const wants = await call({ action: "create-list", name: "Wants" }, headers);
  assert.equal(wants.body.list.name, "Wants");
  const again = await call({ action: "create-list", name: "wants" }, headers);
  assert.equal(again.body.error, "duplicate_list");
  const minted = await call({
    action: "save-item",
    listId: lists.body.lists[0].id,
    figureName: "Luke Skywalker",
    figureGrade: "Mint"
  }, headers);
  assert.equal(minted.statusCode, 400);
  const saved = await call({
    action: "save-item",
    listId: lists.body.lists[0].id,
    figureName: "Luke Skywalker",
    factory: "Unitoy",
    mould: "F1",
    coo: "Hong Kong",
    figureGrade: "Near Mint",
    notes: "Farmboy",
    ownedOn: "2026-10-11",
    accessories: [{ name: "lightsaber", variant: "double telescoping", grade: "Fine" }]
  }, headers);
  assert.equal(saved.statusCode, 200);
  assert.equal(saved.body.item.factory, "Unitoy");
  assert.equal(saved.body.item.accessories[0].name, "lightsaber");
  const moved = await call({ action: "move-item", itemId: saved.body.item.id, listId: wants.body.list.id }, headers);
  assert.equal(moved.body.item.listName, "Wants");
  const edited = await call({
    action: "update-item",
    itemId: saved.body.item.id,
    figureName: "Luke Skywalker",
    figureGrade: "Very Fine",
    accessories: [{ name: "lightsaber", variant: "DT", grade: "Good" }]
  }, headers);
  assert.equal(edited.body.item.figureGrade, "Very Fine");
  assert.equal(edited.body.item.accessories[0].variant, "DT");
  const checklist = await call({ action: "checklist" }, headers);
  const luke = checklist.body.figures.find(figure => figure.name === "Luke Skywalker");
  assert.equal(luke.owned, true);
  assert.equal(checklist.body.owned >= 1, true);
  assert.equal(checklist.body.needed, checklist.body.total - checklist.body.owned);
  assert.equal(checklist.body.total >= 90, true);
  const removed = await call({ action: "delete-item", itemId: saved.body.item.id }, headers);
  assert.equal(removed.body.ok, true);
  const after = await call({ action: "checklist" }, headers);
  assert.equal(after.body.figures.find(figure => figure.name === "Luke Skywalker").owned, false);
});

await test("a lapsed dev plan is refused at the save gate", async () => {
  process.env.MEMBERS_DEV = "1";
  process.env.MEMBERS_DEV_PLAN = "lapsed";
  const signIn = await call({ action: "dev-sign-in", email: "lapsed@example.com", provider: "facebook" });
  const headers = { cookie: signIn.headers["set-cookie"].split(";")[0] };
  const me = await call({ action: "me" }, headers);
  assert.equal(me.body.member.canSave, false);
  const save = await call({ action: "save-item", figureName: "Jawa", figureGrade: "Fine" }, headers);
  assert.equal(save.statusCode, 403);
  assert.equal(save.body.message, SAVE_BLOCKED_MESSAGE);
  const lists = await call({ action: "lists" }, headers);
  assert.equal(lists.statusCode, 200);
});

await test("an oversized photo is refused and a file store reloads", async () => {
  const huge = validateItem({ figureName: "Jawa", photo: `data:image/jpeg;base64,${"A".repeat(200_000)}` });
  assert.equal(huge.error, "photo_too_large");
  const file = path.join(os.tmpdir(), `sw7885-members-${Date.now()}.json`);
  const store = createFileStore(file);
  await store.ensureMember({ id: "dev:email:a@b.co", email: "a@b.co", plan: "free" });
  const lists = await store.listsFor("dev:email:a@b.co");
  const saved = await store.saveItem(lists[0].id && "dev:email:a@b.co", lists[0].id, validateItem({
    figureName: "Jawa",
    figureGrade: "Good",
    accessories: [{ name: "blaster", grade: "Fair" }]
  }).item);
  const reloaded = createFileStore(file);
  const items = await reloaded.allItems("dev:email:a@b.co");
  assert.equal(items.length, 1);
  assert.equal(items[0].figureName, "Jawa");
  assert.equal(saved.item.accessories[0].grade, "Fair");
  fs.unlinkSync(file);
});

await test("an identification becomes a save draft, and Save to… stays gated", () => {
  let draft = applyIdentification(null, {
    topic: "image_identified",
    itemKind: "figure",
    displayName: "Luke Skywalker",
    figure: "luke_skywalker",
    visibleAccessories: ["lightsaber"]
  });
  draft = applyIdentification(draft, { topic: "accessory_factory", figure: "Luke Skywalker", factory: "Unitoy guide", accessory: "lightsaber" });
  assert.equal(draft.figureName, "Luke Skywalker");
  assert.equal(draft.factory, "Unitoy");
  assert.equal(draft.accessories[0].name, "lightsaber");
  assert.equal(identificationReady(draft), true);
  assert.equal(saveActionVisible({ enabled: false, signedIn: true, identified: true, canSave: true }), false);
  assert.equal(saveActionVisible({ enabled: true, signedIn: false, identified: true, canSave: true }), false);
  assert.equal(saveActionVisible({ enabled: true, signedIn: true, identified: false, canSave: true }), false);
  assert.equal(saveActionVisible({ enabled: true, signedIn: true, identified: true, canSave: false }), false);
  assert.equal(saveActionVisible({ enabled: true, signedIn: true, identified: true, canSave: true }), true);
});

await test("the page wires members without offering a removed provider, and the setup list matches", () => {
  const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
  assert.match(page, /id="memberBar"/);
  assert.match(page, /mountMembers/);
  assert.match(page, /noteIdentification/);
  const names = ["members-ui.js", "sso-callback.html", "api/members.js", "lib/members-auth.js", "docs/MEMBERS-SETUP.md", "index.html"];
  const blob = names.map(name => fs.readFileSync(path.join(root, name), "utf8")).join("\n");
  assert.equal(/\bapple\b/i.test(blob), false);
  assert.match(blob, /oauth_google/);
  assert.match(blob, /oauth_facebook/);
  assert.match(blob, /CLERK_PUBLISHABLE_KEY/);
  assert.match(blob, /CLERK_SECRET_KEY/);
  assert.match(blob, /DATABASE_URL/);
  assert.match(blob, /Personal Collection/);
});

console.log(`\n${passed} passed, ${failed} failed`);
restoreEnv();
if (failed) process.exit(1);
