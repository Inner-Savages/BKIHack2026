<script>
  import { activeCodes } from '../lib/stores.js';

  let inputCode = '';
  let result = null;
  let inputDisabled = false;

  $: verifyEnabled = inputCode.length === 6 && !inputDisabled;

  function handleInput(e) {
    inputCode = e.target.value.replace(/[^0-9]/g, '').slice(0, 6);
  }

  function handleVerify() {
    const codes = $activeCodes;
    const entry = codes[inputCode];

    if (!entry) {
      result = { type: 'fail', icon: '✗', title: 'Kod nieważny', sub: 'Kod nie istnieje lub wygasł' };
      return;
    }

    if (entry.used) {
      result = { type: 'fail', icon: '✗', title: 'Kod już użyty', sub: 'Kody są jednorazowe — wygeneruj nowy w mObywatel' };
      return;
    }

    if (Date.now() > entry.expiry) {
      activeCodes.update((c) => {
        const updated = { ...c };
        delete updated[inputCode];
        return updated;
      });
      result = { type: 'fail', icon: '⏰', title: 'Kod wygasł', sub: 'Minęło 5 minut — wygeneruj nowy kod' };
      return;
    }

    activeCodes.update((c) => ({
      ...c,
      [inputCode]: { ...c[inputCode], used: true },
    }));

    result = { type: 'success', icon: '✓', title: 'Wiek zweryfikowany!', sub: 'Dostęp przyznany. Nie znamy Twojej tożsamości.' };
    inputDisabled = true;
  }

  function handleReset() {
    inputCode = '';
    result = null;
    inputDisabled = false;
  }
</script>

<div class="site-frame">
  <!-- Browser bar -->
  <div class="browser-bar">
    <div class="browser-dots">
      <div class="browser-dot dot-red"></div>
      <div class="browser-dot dot-yellow"></div>
      <div class="browser-dot dot-green"></div>
    </div>
    <div class="browser-url">
      <span class="lock">🔒</span> https://example-adult.pl/weryfikacja
    </div>
  </div>

  <!-- Site content -->
  <div class="site-content">
    <div class="site-logo">🔞</div>
    <div class="site-title">Weryfikacja wieku</div>
    <div class="site-subtitle">Wpisz 6-cyfrowy kod z aplikacji mObywatel</div>

    <div class="site-card">
      <div class="site-card-title">Kod weryfikacyjny</div>
      <input
        type="text"
        class="site-input"
        maxlength="6"
        placeholder="——————"
        inputmode="numeric"
        pattern="[0-9]*"
        value={inputCode}
        disabled={inputDisabled}
        on:input={handleInput}
      />
      <button class="site-btn" disabled={!verifyEnabled} on:click={handleVerify}>
        Zweryfikuj wiek
      </button>
    </div>

    {#if result}
      <div class="site-result {result.type === 'success' ? 'result-success' : 'result-fail'}">
        <div class="result-icon">{result.icon}</div>
        <div class="result-text">{result.title}</div>
        <div class="result-sub">{result.sub}</div>
      </div>
      <button class="site-reset" on:click={handleReset}>
        {result.type === 'success' ? 'Zweryfikuj kolejny kod' : 'Spróbuj ponownie'}
      </button>
    {/if}

    <div class="site-info">
      <strong>Prywatność:</strong> Ta strona otrzymuje wyłącznie odpowiedź TAK/NIE.<br />
      Nie znamy Twojego imienia, PESELu ani żadnych danych osobowych.
    </div>
  </div>
</div>

<style>
  .site-frame {
    width: 480px;
    min-height: 740px;
    background: #1a1a2e;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
  }

  /* ── Browser bar ── */
  .browser-bar {
    background: #2d2d44;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .browser-dots { display: flex; gap: 6px; }
  .browser-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }
  .dot-red { background: #ff5f57; }
  .dot-yellow { background: #febc2e; }
  .dot-green { background: #28c840; }
  .browser-url {
    flex: 1;
    background: #1a1a2e;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    color: #888;
    font-family: monospace;
  }
  .lock { color: #28c840; }

  /* ── Site content ── */
  .site-content {
    flex: 1;
    padding: 32px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .site-logo { font-size: 32px; margin-bottom: 8px; }
  .site-title {
    color: #fff;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
    font-family: 'Inter', sans-serif;
  }
  .site-subtitle {
    color: #888;
    font-size: 13px;
    margin-bottom: 32px;
    font-family: 'Inter', sans-serif;
  }

  /* ── Site card ── */
  .site-card {
    background: #2d2d44;
    border-radius: 16px;
    padding: 24px;
    width: 100%;
    margin-bottom: 16px;
  }
  .site-card-title {
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 16px;
    font-family: 'Inter', sans-serif;
  }

  /* ── Code input ── */
  .site-input {
    width: 100%;
    padding: 16px;
    background: #1a1a2e;
    border: 2px solid #3d3d5c;
    border-radius: 12px;
    color: #fff;
    font-size: 28px;
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    text-align: center;
    letter-spacing: 10px;
    outline: none;
    transition: border-color 0.2s;
    font-variant-numeric: tabular-nums;
  }
  .site-input:focus { border-color: #7c4dff; }
  .site-input::placeholder {
    color: #555;
    font-size: 16px;
    letter-spacing: 2px;
    font-weight: 400;
  }
  .site-input:disabled { opacity: 0.5; cursor: not-allowed; }

  /* ── Verify button ── */
  .site-btn {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    margin-top: 16px;
    transition: transform 0.1s, opacity 0.2s;
    background: linear-gradient(135deg, #7c4dff, #651fff);
    color: white;
  }
  .site-btn:active { transform: scale(0.98); }
  .site-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* ── Result ── */
  .site-result {
    width: 100%;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    margin-top: 0;
    animation: fadeIn 0.4s;
  }
  .result-success {
    background: rgba(46, 125, 50, 0.15);
    border: 2px solid #2e7d32;
  }
  .result-fail {
    background: rgba(196, 30, 58, 0.15);
    border: 2px solid #c41e3a;
  }
  .result-icon { font-size: 40px; margin-bottom: 8px; }
  .result-text { color: #fff; font-size: 16px; font-weight: 600; font-family: 'Inter', sans-serif; }
  .result-sub { color: #aaa; font-size: 12px; margin-top: 6px; font-family: 'Inter', sans-serif; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* ── Reset button ── */
  .site-reset {
    background: none;
    border: 1px solid #3d3d5c;
    color: #aaa;
    padding: 10px 20px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    cursor: pointer;
    margin-top: 12px;
    transition: border-color 0.2s, color 0.2s;
  }
  .site-reset:hover { border-color: #7c4dff; color: #fff; }

  /* ── Privacy info ── */
  .site-info {
    color: #666;
    font-size: 11px;
    text-align: center;
    margin-top: 16px;
    line-height: 1.5;
    font-family: 'Inter', sans-serif;
  }
  .site-info strong { color: #aaa; }
</style>
