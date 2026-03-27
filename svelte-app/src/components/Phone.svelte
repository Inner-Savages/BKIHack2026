<script>
  import { onDestroy } from 'svelte';
  import { activeCodes } from '../lib/stores.js';
  import { randomHex, generateCode, formatCode, sleep, buildCryptoSteps } from '../lib/crypto.js';

  let step = 1;
  let cryptoLog = [];
  let processingText = 'Zaślepiam token...';
  let processingSubtext = 'Generowanie losowego czynnika zaślepiającego';

  let code = null;
  let codeExpiry = null;
  let timerInterval = null;
  let timerRemaining = 300000;
  let codeExpiredLocally = false;
  let copySuccess = false;

  $: isCodeUsed = code !== null && ($activeCodes[code]?.used === true);
  $: timerPct = 100 * timerRemaining / 300000;
  $: timerColorClass = timerPct > 40 ? 'timer-ok' : timerPct > 15 ? 'timer-warn' : 'timer-danger';
  $: barColorClass = timerPct > 40 ? 'fill-ok' : timerPct > 15 ? 'fill-warn' : 'fill-danger';
  $: timerExpired = timerRemaining <= 0 || codeExpiredLocally;
  $: formattedTime = timerExpired ? 'WYGASŁ' : formatTimerDisplay(timerRemaining);
  $: headerGreen = step === 3;

  function formatTimerDisplay(ms) {
    const totalSec = Math.ceil(ms / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${min}:${String(sec).padStart(2, '0')}`;
  }

  function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerRemaining = Math.max(0, codeExpiry - Date.now());
    codeExpiredLocally = false;

    timerInterval = setInterval(() => {
      timerRemaining = Math.max(0, codeExpiry - Date.now());
      if (timerRemaining <= 0) {
        clearInterval(timerInterval);
        codeExpiredLocally = true;
        activeCodes.update((codes) => {
          const updated = { ...codes };
          if (code && updated[code]) delete updated[code];
          return updated;
        });
      }
    }, 200);
  }

  async function handleGenerate() {
    if (code) {
      activeCodes.update((codes) => {
        const updated = { ...codes };
        delete updated[code];
        return updated;
      });
    }
    if (timerInterval) clearInterval(timerInterval);
    code = null;
    copySuccess = false;
    codeExpiredLocally = false;

    step = 2;
    cryptoLog = [];

    const steps = buildCryptoSteps();

    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      processingText = s.text;
      processingSubtext = s.sub;

      if (i === steps.length - 1) {
        const newCode = generateCode();
        code = newCode;
        codeExpiry = Date.now() + 300000;
        timerRemaining = 300000;

        activeCodes.update((codes) => ({
          ...codes,
          [newCode]: { expiry: codeExpiry, used: false },
        }));

        cryptoLog = [
          ...cryptoLog,
          `<strong>Rząd B:</strong> Wygenerowano kod <strong>${formatCode(newCode)}</strong><br>Tożsamość: NIEZNANA (ślepy podpis uniemożliwia identyfikację)`,
        ];
      } else if (s.log) {
        cryptoLog = [...cryptoLog, s.log()];
      }

      await sleep(600 + Math.random() * 400);
    }

    await sleep(500);
    startTimer();
    step = 3;
  }

  async function handleCopy() {
    if (!code || isCodeUsed || timerExpired) return;
    try {
      await navigator.clipboard.writeText(code);
    } catch (_) {}
    copySuccess = true;
    setTimeout(() => (copySuccess = false), 2000);
  }

  onDestroy(() => {
    if (timerInterval) clearInterval(timerInterval);
  });
</script>

<div class="phone">
  <!-- Notch -->
  <div class="notch"></div>

  <!-- ── EKRAN 1: Tożsamość + generuj token ── -->
  {#if step === 1}
    <div class="header header-red">
      <div class="header-logo">mObywatel</div>
      <div class="header-icons">
        <svg class="header-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        <svg class="header-icon" viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
      </div>
    </div>

    <div class="status-date">Stan na dzień 27 marca 2026</div>

    <div class="content">
      <div class="card">
        <div class="user-card">
          <div class="user-photo">👤</div>
          <div class="user-name">
            <div class="first">JAN STANISŁAW</div>
            <div class="last">KOWALSKI</div>
            <div class="pesel-label">Nr PESEL</div>
            <div class="pesel">95030112345</div>
          </div>
        </div>
        <div class="info-row">
          <span class="info-label">Data urodzenia</span>
          <span class="info-value">01.03.1995</span>
        </div>
        <div class="info-row">
          <span class="info-label">Wiek</span>
          <span class="info-value">31 lat</span>
        </div>
        <div class="info-row">
          <span class="info-label">Obywatelstwo</span>
          <span class="info-value flag-row">
            <span class="flag-pl">
              <span class="flag-white"></span>
              <span class="flag-red-stripe"></span>
            </span>
            Polskie
          </span>
        </div>
        <div class="badge badge-success">
          <span>✓</span> Tożsamość zweryfikowana
        </div>
      </div>

      <div class="section-title">Weryfikacja wieku</div>

      <div class="card">
        <div class="card-header">
          <div class="card-icon card-icon-blue">🔒</div>
          <div>
            <div class="card-title">Potwierdź pełnoletność</div>
            <div class="card-subtitle">Anonimowa weryfikacja 18+</div>
          </div>
        </div>
        <div class="crypto-viz">
          <span>🎫 Token</span>
          <span class="crypto-arrow">→</span>
          <span>📦 Koperta</span>
          <span class="crypto-arrow">→</span>
          <span>✍️ Podpis</span>
        </div>
        <button class="btn btn-primary" on:click={handleGenerate}>
          Generuj anonimowy token
        </button>
        <div class="privacy-shield">
          <div class="shield-text">
            Twój token zostanie <strong>zaślepiony</strong> — Rząd A podpisze go
            <strong>nie widząc zawartości</strong>
          </div>
        </div>
      </div>

      <div class="steps">
        <div class="step-dot active"></div>
        <div class="step-dot"></div>
        <div class="step-dot"></div>
      </div>
    </div>

    <div class="bottom-nav">
      <div class="nav-item active"><span class="nav-icon">🏠</span><span>Główna</span></div>
      <div class="nav-item"><span class="nav-icon">📄</span><span>Dokumenty</span></div>
      <div class="nav-item"><span class="nav-icon">🔔</span><span>Powiadomienia</span></div>
    </div>
  {/if}

  <!-- ── EKRAN 2: Przetwarzanie kryptograficzne ── -->
  {#if step === 2}
    <div class="header header-red">
      <div class="header-logo">mObywatel</div>
      <div class="header-icons">
        <svg class="header-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        <svg class="header-icon" viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
      </div>
    </div>

    <div class="status-date">Przetwarzanie...</div>

    <div class="content">
      <div class="card">
        <div class="lock-container">
          <div class="lock-icon spin">⏳</div>
          <div class="lock-text">{processingText}</div>
          <div class="lock-subtext">{processingSubtext}</div>
        </div>
      </div>

      <div class="section-title">Dziennik kryptograficzny</div>
      <div class="crypto-log-wrap">
        {#each cryptoLog as entry}
          <div class="log-entry">{@html entry}</div>
        {/each}
      </div>

      <div class="steps">
        <div class="step-dot done"></div>
        <div class="step-dot active"></div>
        <div class="step-dot"></div>
      </div>
    </div>

    <div class="bottom-nav">
      <div class="nav-item active"><span class="nav-icon">🏠</span><span>Główna</span></div>
      <div class="nav-item"><span class="nav-icon">📄</span><span>Dokumenty</span></div>
      <div class="nav-item"><span class="nav-icon">🔔</span><span>Powiadomienia</span></div>
    </div>
  {/if}

  <!-- ── EKRAN 3: Kod aktywny ── -->
  {#if step === 3}
    <div class="header header-green">
      <div class="header-logo">mObywatel</div>
      <div class="header-icons">
        <svg class="header-icon" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
        <svg class="header-icon" viewBox="0 0 24 24"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
      </div>
    </div>

    <div class="status-date">Kod aktywny</div>

    <div class="content">
      <div class="card">
        <div class="lock-container">
          <div class="lock-icon pulse">🛡️</div>
          <div class="lock-text">Wiek zweryfikowany anonimowo</div>
          <div class="lock-subtext">Żaden podmiot nie zna Twojej tożsamości i kodu jednocześnie</div>
        </div>
      </div>

      <div class="card">
        <div class="code-display">
          <div class="code-label">Twój jednorazowy kod</div>
          <div class="code-number" style="opacity: {timerExpired ? 0.3 : 1}">
            {code ? formatCode(code) : '--- ---'}
          </div>
          <div class="code-timer {timerColorClass}">
            <span>⏱️</span>
            <span>{formattedTime}</span>
          </div>
          <div class="timer-bar">
            <div
              class="timer-fill {barColorClass}"
              style="width: {timerPct}%"
            ></div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="info-row">
          <span class="info-label">Użycia</span>
          <span class="info-value" style="color: {isCodeUsed ? '#c41e3a' : ''}">
            {isCodeUsed ? 'Wykorzystany ✓' : 'Jednorazowy'}
          </span>
        </div>
        <div class="info-row">
          <span class="info-label">Czas życia</span>
          <span class="info-value">5 minut</span>
        </div>
        <div class="info-row">
          <span class="info-label">Strona widzi</span>
          <span class="info-value">Tylko kod</span>
        </div>
        <button class="btn btn-green" on:click={handleCopy}>
          {copySuccess ? 'Skopiowano! ✓' : 'Kopiuj kod'}
        </button>
      </div>

      <button class="btn btn-primary" style="margin-top: 4px" on:click={handleGenerate}>
        Generuj nowy kod
      </button>

      <div class="steps">
        <div class="step-dot done"></div>
        <div class="step-dot done"></div>
        <div class="step-dot active"></div>
      </div>
    </div>

    <div class="bottom-nav">
      <div class="nav-item active"><span class="nav-icon">🏠</span><span>Główna</span></div>
      <div class="nav-item"><span class="nav-icon">📄</span><span>Dokumenty</span></div>
      <div class="nav-item"><span class="nav-icon">🔔</span><span>Powiadomienia</span></div>
    </div>
  {/if}
</div>

<style>
  .phone {
    width: 360px;
    height: 740px;
    background: #f5f5f7;
    border-radius: 44px;
    overflow: hidden;
    box-shadow:
      0 25px 60px rgba(0, 0, 0, 0.3),
      0 0 0 2px rgba(0, 0, 0, 0.1),
      inset 0 0 0 2px rgba(255, 255, 255, 0.1);
    position: relative;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
  }

  .notch {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 120px;
    height: 28px;
    background: #1a1a1a;
    border-radius: 0 0 18px 18px;
    z-index: 100;
  }

  /* ── Header ── */
  .header {
    padding: 44px 20px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }
  .header-red { background: linear-gradient(135deg, #d4234a 0%, #c41e3a 100%); }
  .header-green { background: linear-gradient(135deg, #2e7d32 0%, #1b5e20 100%); }
  .header-logo { color: white; font-size: 18px; font-weight: 600; letter-spacing: 0.5px; }
  .header-icons { display: flex; gap: 14px; }
  .header-icon { width: 22px; height: 22px; fill: white; opacity: 0.9; }

  /* ── Status date ── */
  .status-date {
    font-size: 11px;
    color: #888;
    text-align: center;
    padding: 8px;
    flex-shrink: 0;
  }

  /* ── Content ── */
  .content {
    flex: 1;
    padding: 10px 16px 16px;
    overflow-y: auto;
  }

  /* ── Card ── */
  .card {
    background: white;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 10px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
  }
  .card-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }
  .card-icon-blue { background: #e3f2fd; }
  .card-title { font-size: 15px; font-weight: 600; color: #1a1a1a; }
  .card-subtitle { font-size: 11px; color: #888; margin-top: 2px; }

  /* ── User card ── */
  .user-card {
    display: flex;
    gap: 14px;
    align-items: center;
    padding-bottom: 14px;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 10px;
  }
  .user-photo {
    width: 58px;
    height: 72px;
    background: linear-gradient(135deg, #ddd, #ccc);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #999;
    flex-shrink: 0;
    border: 2px solid #e0e0e0;
  }
  .first { font-size: 14px; color: #888; }
  .last { font-size: 17px; font-weight: 700; color: #1a1a1a; }
  .pesel-label { font-size: 10px; color: #aaa; margin-top: 6px; }
  .pesel { font-size: 13px; font-weight: 500; color: #1a1a1a; }

  /* ── Info rows ── */
  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
  }
  .info-row:last-child { border-bottom: none; }
  .info-label { font-size: 12px; color: #888; }
  .info-value { font-size: 13px; font-weight: 500; color: #1a1a1a; }
  .flag-row { display: flex; align-items: center; gap: 6px; }
  .flag-pl {
    display: inline-flex;
    width: 24px;
    height: 16px;
    border-radius: 3px;
    overflow: hidden;
    flex-direction: column;
    border: 1px solid #e0e0e0;
  }
  .flag-white { background: white; flex: 1; }
  .flag-red-stripe { background: #dc143c; flex: 1; }

  /* ── Badge ── */
  .badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 10px;
    margin-top: 10px;
    font-size: 13px;
    font-weight: 500;
  }
  .badge-success { background: #e8f5e9; color: #2e7d32; }

  /* ── Section title ── */
  .section-title {
    font-size: 12px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 8px 0 6px;
  }

  /* ── Crypto viz ── */
  .crypto-viz {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 10px;
    margin: 8px 0;
    font-size: 11px;
    color: #666;
  }
  .crypto-arrow { font-size: 14px; color: #c41e3a; }

  /* ── Buttons ── */
  .btn {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
    margin-top: 6px;
    transition: transform 0.1s, opacity 0.2s;
  }
  .btn:active { transform: scale(0.98); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-primary { background: linear-gradient(135deg, #c41e3a, #d4234a); color: white; }
  .btn-green { background: linear-gradient(135deg, #2e7d32, #43a047); color: white; }

  /* ── Privacy shield ── */
  .privacy-shield { text-align: center; padding: 8px; }
  .shield-text { font-size: 11px; color: #888; line-height: 1.5; }
  .shield-text :global(strong) { color: #2e7d32; }

  /* ── Steps dots ── */
  .steps { display: flex; justify-content: center; gap: 8px; margin: 12px 0; }
  .step-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ddd;
    transition: background 0.3s;
  }
  .step-dot.active { background: #c41e3a; }
  .step-dot.done { background: #2e7d32; }

  /* ── Lock / processing ── */
  .lock-container { text-align: center; padding: 16px; }
  .lock-icon { font-size: 48px; }
  .lock-icon.pulse { animation: pulse 2s ease-in-out infinite; }
  .lock-icon.spin { animation: spin 1.5s linear infinite; }
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
  }
  @keyframes spin {
    0% { display: inline-block; }
    50% { opacity: 0.6; }
    100% { opacity: 1; }
  }
  .lock-text { margin-top: 8px; font-size: 14px; color: #2e7d32; font-weight: 600; }
  .lock-subtext { font-size: 11px; color: #888; margin-top: 4px; }

  /* ── Crypto log ── */
  .crypto-log-wrap { margin-bottom: 8px; }
  .log-entry {
    font-size: 11px;
    padding: 8px 10px;
    margin: 4px 0;
    border-radius: 8px;
    background: #f8f9fa;
    color: #555;
    line-height: 1.4;
    animation: fadeIn 0.3s;
  }
  .log-entry :global(strong) { color: #1a1a1a; }
  .log-entry :global(em) { color: #aaa; }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* ── Code display ── */
  .code-display { text-align: center; padding: 20px 12px; }
  .code-label {
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
  }
  .code-number {
    font-size: 44px;
    font-weight: 800;
    letter-spacing: 8px;
    color: #1a1a1a;
    font-variant-numeric: tabular-nums;
    transition: opacity 0.3s;
  }
  .code-timer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-top: 10px;
    font-size: 14px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
  .timer-ok { color: #2e7d32; }
  .timer-warn { color: #f57f17; }
  .timer-danger { color: #c41e3a; }
  .timer-bar {
    width: 100%;
    height: 4px;
    background: #f0f0f0;
    border-radius: 2px;
    margin-top: 10px;
    overflow: hidden;
  }
  .timer-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.2s linear, background-color 0.5s;
  }
  .fill-ok { background: #2e7d32; }
  .fill-warn { background: #f57f17; }
  .fill-danger { background: #c41e3a; }

  /* ── Bottom nav ── */
  .bottom-nav {
    display: flex;
    justify-content: space-around;
    padding: 8px 0 22px;
    border-top: 1px solid #e8e8e8;
    background: white;
    flex-shrink: 0;
  }
  .nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    font-size: 10px;
    color: #888;
  }
  .nav-item.active { color: #c41e3a; }
  .nav-icon { font-size: 18px; }
</style>
