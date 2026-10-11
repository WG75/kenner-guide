import crypto from "node:crypto";

export const DEV_COOKIE = "sw7885_dev";
const PROVIDERS = ["email", "google", "facebook"];

export function membersMode(env = process.env) {
  const hasClerk = Boolean(env.CLERK_PUBLISHABLE_KEY && env.CLERK_SECRET_KEY);
  if (env.VERCEL_ENV === "production") return hasClerk ? "clerk" : "off";
  if (env.MEMBERS_DEV === "1") return "dev";
  if (hasClerk) return "clerk";
  return "off";
}

export function publicConfig(env = process.env) {
  const mode = membersMode(env);
  if (mode === "off") return { enabled: false, mode: "off", providers: [] };
  return {
    enabled: true,
    mode,
    providers: PROVIDERS,
    publishableKey: mode === "clerk" ? env.CLERK_PUBLISHABLE_KEY : ""
  };
}

function devSecret(env) {
  return env.MEMBERS_DEV_SECRET || "sw7885-local-dev-only";
}

export function signDevSession(email, provider, env = process.env) {
  const cleanProvider = PROVIDERS.includes(provider) ? provider : "email";
  const payload = Buffer.from(JSON.stringify({
    email: String(email || "").trim().toLowerCase(),
    provider: cleanProvider,
    exp: Date.now() + 1000 * 60 * 60 * 24 * 14
  })).toString("base64url");
  const sig = crypto.createHmac("sha256", devSecret(env)).update(payload).digest("base64url");
  return `${payload}.${sig}`;
}

export function readDevSession(cookieHeader, env = process.env) {
  const raw = String(cookieHeader || "");
  const match = raw.match(new RegExp(`(?:^|;\\s*)${DEV_COOKIE}=([^;]+)`));
  if (!match) return null;
  const token = decodeURIComponent(match[1]);
  const split = token.split(".");
  if (split.length !== 2) return null;
  const [payload, sig] = split;
  const expected = crypto.createHmac("sha256", devSecret(env)).update(payload).digest("base64url");
  const left = Buffer.from(sig);
  const right = Buffer.from(expected);
  if (left.length !== right.length || !crypto.timingSafeEqual(left, right)) return null;
  try {
    const parsed = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!parsed || !parsed.email || !parsed.exp || parsed.exp < Date.now()) return null;
    if (!PROVIDERS.includes(parsed.provider)) return null;
    return parsed;
  } catch (err) {
    return null;
  }
}

export function devCookie(token) {
  const value = token ? `${DEV_COOKIE}=${token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=1209600` : `${DEV_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`;
  return value;
}

export function devMemberFromSession(session, env = process.env) {
  const plan = env.MEMBERS_DEV_PLAN || "free";
  return {
    id: `dev:${session.provider}:${session.email}`,
    email: session.email,
    provider: session.provider,
    plan
  };
}

export async function readMember(req, env = process.env) {
  const mode = membersMode(env);
  if (mode === "off") return null;
  if (mode === "dev") {
    const header = req.headers?.cookie || req.headers?.Cookie || "";
    const session = readDevSession(header, env);
    if (!session) return null;
    return devMemberFromSession(session, env);
  }
  const header = req.headers?.authorization || req.headers?.Authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7).trim() : "";
  if (!token) return null;
  const { verifyToken, createClerkClient } = await import("@clerk/backend");
  const claims = await verifyToken(token, { secretKey: env.CLERK_SECRET_KEY });
  const client = createClerkClient({ secretKey: env.CLERK_SECRET_KEY });
  const user = await client.users.getUser(claims.sub);
  const primary = user.primaryEmailAddress?.emailAddress
    || (user.emailAddresses || []).find(entry => entry.id === user.primaryEmailAddressId)?.emailAddress
    || (user.emailAddresses || [])[0]?.emailAddress
    || "";
  const metadata = user.publicMetadata && typeof user.publicMetadata === "object" ? user.publicMetadata : {};
  const plan = typeof metadata.plan === "string" && metadata.plan ? metadata.plan : "free";
  return { id: claims.sub, email: primary, provider: "clerk", plan };
}
