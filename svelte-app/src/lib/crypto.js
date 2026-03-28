/**
 * Warstwa komunikacji z backendem FastAPI.
 *
 * Każda funkcja odpowiada jednemu krokowi kryptograficznego przepływu.
 * Operacje zaślepienia/odślepienia (BigInt) są wykonywane tutaj — po stronie klienta.
 */
import {
  sha256ToBigInt,
  blindToken,
  unblind,
  hexToBigInt,
  bigIntToHex,
} from './bigint-rsa.js';

const API_BASE = '/api';

/**
 * Formatuje 6-cyfrowy kod: "123456" → "123 456"
 */
export function formatCode(code) {
  return code.slice(0, 3) + ' ' + code.slice(3);
}

/**
 * Promise-based sleep.
 */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ── Krok 1: Pobranie klucza publicznego Gov A ─────────────────────

/**
 * Pobiera klucz publiczny RSA Gov A.
 * @returns {{ e: bigint, n: bigint, eHex: string, nHex: string }}
 */
export async function fetchPublicKey() {
  const res = await fetch(`${API_BASE}/gov-a/public-key`);
  if (!res.ok) throw new Error(`Gov A public-key: ${res.status}`);
  const data = await res.json();
  return {
    eHex: data.e,
    nHex: data.n,
    e: hexToBigInt(data.e),
    n: hexToBigInt(data.n),
  };
}

// ── Krok 2: Generowanie tokenu i zaślepienie ─────────────────────

/**
 * Generuje losowy token, oblicza jego hash i zaślepia go dla Gov A.
 *
 * Operacja zaślepienia dzieje się w PRZEGLĄDARCE — serwer nigdy nie zobaczy
 * oryginalnego tokenu.
 *
 * @param {bigint} e - klucz publiczny Gov A
 * @param {bigint} n - modulus Gov A
 * @returns {{ tokenHex, tokenHashBigInt, tokenHashHex, blinded, blindingR }}
 */
export async function generateAndBlindToken(e, n) {
  // Losowy token (64 bajty → hex string)
  const tokenBytes = new Uint8Array(32);
  crypto.getRandomValues(tokenBytes);
  const tokenHex = '0x' + Array.from(tokenBytes).map(b => b.toString(16).padStart(2, '0')).join('');

  // Hash tokenu jako BigInt (mod n dla RSA)
  const rawHash = await sha256ToBigInt(tokenHex);
  const tokenHashBigInt = rawHash % n;
  const tokenHashHex = bigIntToHex(tokenHashBigInt);

  // Zaślepienie — r jest tajemnicą klienta
  const { blinded, r } = blindToken(tokenHashBigInt, e, n);

  return {
    tokenHex,
    tokenHashBigInt,
    tokenHashHex,
    blindedHex: bigIntToHex(blinded),
    blindingR: r,
  };
}

// ── Krok 3: Ślepy podpis od Gov A ────────────────────────────────

/**
 * Wysyła PESEL + zaślepiony token do Gov A. Zwraca odślepiony podpis.
 *
 * Gov A widzi: PESEL + zaślepiony token (losowy szum).
 * Gov A NIE WIDZI: oryginalnego tokenu.
 *
 * Odślepienie wykonuje klient (BigInt) — wynik to ważny podpis RSA
 * na oryginalnym tokenie, którego Gov A nigdy nie widział.
 *
 * @returns {{ blindSigHex: string, signatureHex: string, signatureBigInt: bigint }}
 */
export async function requestBlindSign(pesel, blindedHex, blindingR, n) {
  const res = await fetch(`${API_BASE}/gov-a/sign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pesel, blinded_token_hex: blindedHex }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Gov A sign: ${res.status}`);
  }

  const data = await res.json();
  const blindSig = hexToBigInt(data.blind_signature_hex);

  // Odślepienie po stronie klienta
  const signature = unblind(blindSig, blindingR, n);

  return {
    blindSigHex: data.blind_signature_hex,
    signatureHex: bigIntToHex(signature),
    signatureBigInt: signature,
  };
}

// ── Krok 4: Zaślepienie OPRF i wydanie kodu przez Gov B ──────────

/**
 * Pobiera parametry OPRF od Gov B.
 * @returns {{ p: bigint, g: bigint }}
 */
export async function fetchOprfParams() {
  const res = await fetch(`${API_BASE}/gov-b/oprf-params`);
  if (!res.ok) throw new Error(`Gov B oprf-params: ${res.status}`);
  const data = await res.json();
  return { p: hexToBigInt(data.p), g: hexToBigInt(data.g) };
}

/**
 * Żąda wydania kodu od Gov B.
 *
 * Przesyła: anonimowy token hash + podpis Gov A + zaślepione dane OPRF.
 * Gov B NIE ZNA tożsamości użytkownika.
 *
 * @returns {{ code: string, expiresIn: number, blindedOprfHex: string }}
 */
export async function requestCode(tokenHashHex, signatureHex, eHex, nHex, p, g) {
  // Zaślepienie danych OPRF po stronie klienta
  const r = BigInt(Math.floor(Math.random() * 1e15) + 2);
  const dataHash = await sha256ToBigInt(tokenHashHex + Date.now());
  const h = modpow(g, dataHash % (p - 1n), p);
  const blindedOprf = modpow(h, r, p);
  const blindedOprfHex = bigIntToHex(blindedOprf);

  const res = await fetch(`${API_BASE}/gov-b/issue-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token_hash_hex: tokenHashHex,
      signature_hex: signatureHex,
      gov_a_e_hex: eHex,
      gov_a_n_hex: nHex,
      blinded_oprf_hex: blindedOprfHex,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Gov B issue-code: ${res.status}`);
  }

  const data = await res.json();
  return { code: data.code, expiresIn: data.expires_in, blindedOprfHex };
}

// ── Krok 5: Weryfikacja kodu przez Stronę 18+ ────────────────────

/**
 * Weryfikuje kod u Gov B (dla Strony 18+).
 * @returns {{ valid: boolean, reason?: string }}
 */
export async function verifyCode(code) {
  const res = await fetch(`${API_BASE}/gov-b/verify-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  if (!res.ok) throw new Error(`Gov B verify-code: ${res.status}`);
  return res.json();
}

// pomocnicza — duplikat modpow lokalnie dla OPRF
function modpow(base, exp, mod) {
  if (mod === 1n) return 0n;
  let result = 1n;
  base = base % mod;
  while (exp > 0n) {
    if (exp % 2n === 1n) result = (result * base) % mod;
    exp = exp >> 1n;
    base = (base * base) % mod;
  }
  return result;
}
