// Client-side photo resize. The canvas itself is the browser's; these tests
// cover the size rules and that the chat page sends the reduced image.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  PHOTO_MAX_SIDE,
  PHOTO_JPEG_QUALITY,
  PHOTO_MAX_DATA_URL_CHARS,
  PHOTO_TOO_LARGE_MESSAGE,
  uploadScale,
  dataUrlTooLarge,
  preparePhotoForUpload
} from "../photo-upload.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

let passed = 0;
let failed = 0;
async function test(name, fn) {
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

await test("longest side is capped at 1280 and small photos are left alone", () => {
  assert.equal(PHOTO_MAX_SIDE, 1280);
  assert.equal(PHOTO_JPEG_QUALITY, 0.8);
  assert.deepEqual(uploadScale(4000, 3000), { width: 1280, height: 960 });
  assert.deepEqual(uploadScale(800, 600), { width: 800, height: 600 });
  assert.deepEqual(uploadScale(1000, 2000), { width: 640, height: 1280 });
});

await test("a data URL over the budget is refused before it can hit the 4.5 MB body limit", () => {
  assert.equal(PHOTO_MAX_DATA_URL_CHARS < 4_500_000, true);
  assert.equal(dataUrlTooLarge("a".repeat(PHOTO_MAX_DATA_URL_CHARS + 1)), true);
  assert.equal(dataUrlTooLarge("data:image/jpeg;base64,abc"), false);
});

await test("the first quality that fits is the one sent", async () => {
  const hooks = {
    async load() {
      return { width: 3000, height: 2000 };
    },
    async encode(_image, size, quality) {
      assert.deepEqual(size, { width: 1280, height: 853 });
      if (quality === 0.8) return "x".repeat(PHOTO_MAX_DATA_URL_CHARS + 5);
      return `data:image/jpeg;base64,ok-${quality}`;
    }
  };
  const prepared = await preparePhotoForUpload("data:image/jpeg;base64,ORIGINAL", { hooks });
  assert.equal(prepared.ok, true);
  assert.equal(prepared.dataUrl, "data:image/jpeg;base64,ok-0.6");
  assert.equal(prepared.quality, 0.6);
  assert.doesNotMatch(prepared.dataUrl, /ORIGINAL/);
});

await test("still-too-large photos get a friendly error and are not sent", async () => {
  const hooks = {
    async load() {
      return { width: 4000, height: 3000 };
    },
    async encode() {
      return "x".repeat(PHOTO_MAX_DATA_URL_CHARS + 1);
    }
  };
  const prepared = await preparePhotoForUpload("data:image/jpeg;base64,HUGE", { hooks });
  assert.equal(prepared.ok, false);
  assert.equal(prepared.message, PHOTO_TOO_LARGE_MESSAGE);
  assert.equal(prepared.dataUrl, undefined);
});

await test("an unreadable file is a friendly error", async () => {
  const hooks = {
    async load() {
      throw new Error("decode");
    },
    async encode() {
      throw new Error("should not encode");
    }
  };
  const prepared = await preparePhotoForUpload("data:image/heic;base64,nope", { hooks });
  assert.equal(prepared.ok, false);
  assert.match(prepared.message, /JPEG or PNG/);
});

await test("the chat page sends the reduced image, not the original file", () => {
  const page = fs.readFileSync(path.join(root, "index.html"), "utf8");
  assert.match(page, /preparePhotoForUpload\(imageDataUrl\)/);
  assert.match(page, /prepared\.dataUrl/);
  assert.match(page, /if \(!prepared\.ok\)/);
  assert.match(page, /addMessage\("assistant", prepared\.message\)/);
  const sendAt = page.indexOf('askApi(note || "Analyse this uploaded figure photo.", prepared.dataUrl)');
  assert.ok(sendAt > 0, "the identification request should carry the reduced data URL");
  assert.equal(page.includes('askApi(note || "Analyse this uploaded figure photo.", imageDataUrl)'), false);
  assert.equal(page.includes("compressPhoto"), false);
});

console.log(`\n${passed} passed, ${failed} failed`);
if (failed) process.exit(1);
