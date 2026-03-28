const assert = require('node:assert/strict');
const CodeAuth = require('./shared/code-auth.js');

function makeDate(hour, minute) {
  return new Date(2026, 2, 28, hour, minute, 0, 0);
}

// Generated codes should encode minute into the first four digits.
for (let i = 0; i < 200; i += 1) {
  const now = makeDate(12, i % 60);
  const minute = now.getMinutes();
  const code = CodeAuth.generateVerificationCode(now);

  assert.match(code, /^\d{6}$/);
  assert.equal(code.slice(4), String(minute).padStart(2, '0'));

  const encodedPrefix = Number(code.slice(0, 4));
  const recoveredBase = encodedPrefix - minute;
  assert.ok(recoveredBase >= 0);
  assert.equal(recoveredBase % 137, 0);
}

// Valid when exactly 5 minutes old.
{
  const code = '014005'; // (140 - 5) = 135 is not divisible -> invalid, so build a valid one.
  const validCode = '014205'; // (142 - 5) = 137
  const out = CodeAuth.validateVerificationCode(validCode, makeDate(10, 10));
  assert.equal(out.valid, true);
}

// Invalid when older than 5 minutes.
{
  const validCode = '014205'; // minute 05
  const out = CodeAuth.validateVerificationCode(validCode, makeDate(10, 11));
  assert.equal(out.valid, false);
  assert.equal(out.reason, 'expired');
}

// Wrap-around 59 -> 00 should work.
{
  const validCode = '033359'; // (333 - 59) = 274, divisible by 137
  const out = CodeAuth.validateVerificationCode(validCode, makeDate(11, 3));
  assert.equal(out.valid, true);
  assert.equal(out.ageMinutes, 4);
}

// Divisibility rule should reject wrong encoded prefixes.
{
  const invalidCode = '123400'; // (1234 - 0) not divisible by 137
  const out = CodeAuth.validateVerificationCode(invalidCode, makeDate(12, 1));
  assert.equal(out.valid, false);
  assert.equal(out.reason, 'divisibility');
}

console.log('All CodeAuth checks passed.');
