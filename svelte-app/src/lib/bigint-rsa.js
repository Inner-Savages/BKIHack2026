/**
 * Klienckie operacje RSA przy użyciu BigInt (natywne w nowoczesnych przeglądarkach).
 *
 * Implementuje zaślepienie i odślepienie tokenu — te operacje MUSZĄ dziać się
 * po stronie klienta, żeby zachować model prywatności (serwer nigdy nie widzi
 * jednocześnie tożsamości i oryginalnego tokenu).
 *
 * Matematyka ślepych podpisów (Chaum 1983):
 *   zaslep:    blinded = hash(token) × r^e mod n
 *   serwer:    blind_sig = blinded^d mod n
 *   odslep:    sig = blind_sig × r^-1 mod n
 *   weryfikuj: sig^e mod n === hash(token)
 */

/**
 * Modular exponentiation: base^exp mod mod.
 * Używa square-and-multiply aby obsłużyć duże BigInty efektywnie.
 */
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

/**
 * Rozszerzony algorytm Euklidesa — zwraca [gcd, x, y] takie że a*x + b*y = gcd.
 */
function extgcd(a, b) {
  if (b === 0n) return [a, 1n, 0n];
  const [g, x1, y1] = extgcd(b, a % b);
  return [g, y1, x1 - (a / b) * y1];
}

/**
 * Odwrotność modułowa: zwraca a^-1 mod n.
 * Rzuca błąd jeśli gcd(a, n) !== 1.
 */
function modinv(a, n) {
  a = ((a % n) + n) % n;
  const [g, x] = extgcd(a, n);
  if (g !== 1n) throw new Error('Brak odwrotności modularnej — gcd !== 1');
  return ((x % n) + n) % n;
}

/**
 * SHA-256 danych wejściowych (string lub Uint8Array), wynik jako BigInt.
 */
export async function sha256ToBigInt(data) {
  const bytes = typeof data === 'string' ? new TextEncoder().encode(data) : data;
  const hashBuf = await crypto.subtle.digest('SHA-256', bytes);
  const hashArr = new Uint8Array(hashBuf);
  return BigInt('0x' + Array.from(hashArr).map(b => b.toString(16).padStart(2, '0')).join(''));
}

/**
 * Generuje losowego BigInt z przedziału [2, n-1].
 */
function randomBigIntBelow(n) {
  const byteLen = Math.ceil(n.toString(16).length / 2) + 4;
  const bytes = new Uint8Array(byteLen);
  crypto.getRandomValues(bytes);
  const num = BigInt('0x' + Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join(''));
  return (num % (n - 2n)) + 2n;
}

/**
 * Zaślepia hash tokenu przed wysłaniem do Gov A.
 *
 * @param {bigint} tokenHash  - hash tokenu jako BigInt (mod n)
 * @param {bigint} e          - klucz publiczny Gov A (e)
 * @param {bigint} n          - modulus Gov A
 * @returns {{ blinded: bigint, r: bigint }}
 */
export function blindToken(tokenHash, e, n) {
  let r, rInv;
  // Szukamy r odwracalnego mod n
  while (true) {
    r = randomBigIntBelow(n);
    try {
      rInv = modinv(r, n);
      break;
    } catch {
      continue;
    }
  }
  // blinded = tokenHash × r^e mod n
  const rToE = modpow(r, e, n);
  const blinded = (tokenHash * rToE) % n;
  return { blinded, r };
}

/**
 * Odślepia podpis zwrócony przez Gov A.
 *
 * @param {bigint} blindSig   - ślepy podpis z Gov A
 * @param {bigint} r          - czynnik zaślepiający (tylko klient go zna)
 * @param {bigint} n          - modulus Gov A
 * @returns {bigint} - prawdziwy podpis RSA na tokenie
 */
export function unblind(blindSig, r, n) {
  const rInv = modinv(r, n);
  return (blindSig * rInv) % n;
}

/**
 * Weryfikuje podpis RSA (opcjonalnie — do debugowania).
 */
export function verifySignature(tokenHash, sig, e, n) {
  return modpow(sig, e, n) === tokenHash;
}

/**
 * Parsuje hex string do BigInt.
 */
export function hexToBigInt(hex) {
  return BigInt(hex.startsWith('0x') ? hex : '0x' + hex);
}

/**
 * Konwertuje BigInt do hex string z prefiksem 0x.
 */
export function bigIntToHex(n) {
  return '0x' + n.toString(16);
}
