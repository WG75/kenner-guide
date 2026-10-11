/* Resize a collector's photo in the browser before it is posted to /api/chat.
   Vercel rejects a function body over 4.5 MB. A phone JPEG, once base64-encoded
   inside JSON, crosses that line. The longest side and JPEG quality below keep
   a normal photo well under it, and a hard character cap refuses anything that
   is still too big. */

export const PHOTO_MAX_SIDE = 1280;
export const PHOTO_JPEG_QUALITY = 0.8;
export const PHOTO_QUALITY_STEPS = [0.8, 0.6, 0.45];
export const PHOTO_MAX_DATA_URL_CHARS = 3_200_000;

export const PHOTO_TOO_LARGE_MESSAGE =
  "That photo is still too large to send after resizing. Try a smaller photo, or crop in closer on the figure.";

export const PHOTO_UNREADABLE_MESSAGE =
  "Sorry, there was a problem reading that photo. Try a JPEG or PNG.";

export function uploadScale(width, height, maxSide = PHOTO_MAX_SIDE) {
  const w = Math.max(1, Number(width) || 1);
  const h = Math.max(1, Number(height) || 1);
  const scale = Math.min(1, maxSide / Math.max(w, h));
  return {
    width: Math.max(1, Math.round(w * scale)),
    height: Math.max(1, Math.round(h * scale))
  };
}

export function dataUrlTooLarge(dataUrl, limit = PHOTO_MAX_DATA_URL_CHARS) {
  return String(dataUrl || "").length > limit;
}

export async function preparePhotoForUpload(dataUrl, options = {}) {
  const maxSide = options.maxSide ?? PHOTO_MAX_SIDE;
  const qualities = options.qualities ?? PHOTO_QUALITY_STEPS;
  const limit = options.limit ?? PHOTO_MAX_DATA_URL_CHARS;
  const hooks = options.hooks || browserHooks();
  let image;
  try {
    image = await hooks.load(dataUrl);
  } catch (err) {
    return { ok: false, message: PHOTO_UNREADABLE_MESSAGE };
  }
  const size = uploadScale(image.width, image.height, maxSide);
  for (const quality of qualities) {
    let encoded = "";
    try {
      encoded = await hooks.encode(image, size, quality);
    } catch (err) {
      return { ok: false, message: PHOTO_UNREADABLE_MESSAGE };
    }
    if (encoded && !dataUrlTooLarge(encoded, limit)) {
      return { ok: true, dataUrl: encoded, width: size.width, height: size.height, quality };
    }
  }
  return { ok: false, message: PHOTO_TOO_LARGE_MESSAGE };
}

function browserHooks() {
  return {
    load(dataUrl) {
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error("unreadable"));
        img.src = dataUrl;
      });
    },
    encode(image, size, quality) {
      const canvas = document.createElement("canvas");
      canvas.width = size.width;
      canvas.height = size.height;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("no canvas");
      ctx.drawImage(image, 0, 0, size.width, size.height);
      const encoded = canvas.toDataURL("image/jpeg", quality);
      if (!encoded || encoded === "data:,") throw new Error("empty");
      return encoded;
    }
  };
}
