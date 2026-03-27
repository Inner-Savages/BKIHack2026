export function randomHex(len) {
  return (
    '0x' +
    Array.from({ length: len }, () =>
      Math.floor(Math.random() * 16).toString(16)
    ).join('')
  );
}

export function generateCode() {
  return String(Math.floor(100000 + Math.random() * 900000));
}

export function formatCode(code) {
  return code.slice(0, 3) + ' ' + code.slice(3);
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function buildCryptoSteps() {
  return [
    {
      text: 'Zaślepiam token...',
      sub: 'Generowanie losowego czynnika zaślepiającego r',
      log: () =>
        `<strong>Użytkownik:</strong> Token wygenerowany<br>Hash: ${randomHex(16)}...`,
    },
    {
      text: 'Zaślepiam token...',
      sub: 'Obliczam: zaslepiony = token × r^e mod n',
      log: () =>
        `<strong>Użytkownik:</strong> Token zaślepiony<br>Rząd A zobaczy: ${randomHex(16)}... <em>(losowy szum)</em>`,
    },
    {
      text: 'Wysyłam do Rządu A...',
      sub: 'PESEL + zaślepiony token → mObywatel',
      log: () =>
        `<strong>Rząd A:</strong> Weryfikacja PESEL → wiek 31 lat ✓<br>Podpisuję zaślepiony token (nie wiem co to jest!)`,
    },
    {
      text: 'Odślepiam podpis...',
      sub: 'podpis = slepy_podpis × r⁻¹ mod n',
      log: () =>
        `<strong>Użytkownik:</strong> Podpis odślepiony ✓<br>Mam ważny podpis na tokenie, którego Rząd A nigdy nie widział!`,
    },
    {
      text: 'Wysyłam do Rządu B...',
      sub: 'Anonimowy token + podpis Rządu A → NASK',
      log: () =>
        `<strong>Rząd B:</strong> Podpis Rządu A ważny ✓<br>Ktoś anonimowy ma 18+ — nie wiem kto`,
    },
    {
      text: 'Przetwarzam OPRF...',
      sub: 'Serwer oblicza na zaślepionych danych',
      log: () =>
        `<strong>Rząd B:</strong> OPRF przetworzono<br>Wejście: ${randomHex(12)}... Wyjście: ${randomHex(12)}... <em>(oba to szum)</em>`,
    },
    {
      text: 'Generuję kod...',
      sub: 'Kod 6-cyfrowy z TTL 5 minut',
      log: null,
    },
  ];
}
