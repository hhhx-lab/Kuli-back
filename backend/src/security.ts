import { createHmac, pbkdf2Sync, randomBytes, timingSafeEqual } from "node:crypto";

export type TokenPayload = {
  sub: string;
  email: string;
  role: "admin" | "user";
  exp: number;
};

const HASH_ALGORITHM = "sha256";
const HASH_ITERATIONS = 80_000;
const HASH_BYTES = 32;

export function hashPassword(password: string) {
  const salt = randomBytes(18).toString("base64url");
  const hash = pbkdf2Sync(password, salt, HASH_ITERATIONS, HASH_BYTES, HASH_ALGORITHM).toString("base64url");
  return `pbkdf2$${HASH_ITERATIONS}$${salt}$${hash}`;
}

export function verifyPassword(password: string, verifier: string) {
  const [scheme, iterationsText, salt, expectedHash] = verifier.split("$");
  if (scheme !== "pbkdf2" || !iterationsText || !salt || !expectedHash) return false;

  const iterations = Number(iterationsText);
  if (!Number.isInteger(iterations) || iterations < 1) return false;

  const actual = Buffer.from(pbkdf2Sync(password, salt, iterations, HASH_BYTES, HASH_ALGORITHM).toString("base64url"));
  const expected = Buffer.from(expectedHash);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

export function signToken(payload: Omit<TokenPayload, "exp">, secret: string, ttlSeconds = 60 * 60 * 24) {
  const body: TokenPayload = {
    ...payload,
    exp: Math.floor(Date.now() / 1000) + ttlSeconds
  };
  const encoded = base64url(JSON.stringify(body));
  const signature = createHmac("sha256", secret).update(encoded).digest("base64url");
  return `${encoded}.${signature}`;
}

export function verifyToken(token: string, secret: string): TokenPayload | null {
  const [encoded, signature] = token.split(".");
  if (!encoded || !signature) return null;

  const expected = createHmac("sha256", secret).update(encoded).digest("base64url");
  if (!safeEqual(signature, expected)) return null;

  try {
    const payload = JSON.parse(Buffer.from(encoded, "base64url").toString("utf8")) as TokenPayload;
    if (!payload.sub || !payload.email || !payload.role || payload.exp < Math.floor(Date.now() / 1000)) return null;
    if (payload.role !== "admin" && payload.role !== "user") return null;
    return payload;
  } catch {
    return null;
  }
}

function base64url(value: string) {
  return Buffer.from(value).toString("base64url");
}

function safeEqual(left: string, right: string) {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  return leftBuffer.length === rightBuffer.length && timingSafeEqual(leftBuffer, rightBuffer);
}
