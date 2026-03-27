(function() {
    if (sessionStorage.getItem('bki_auth') === '1') return;

    var overlay = document.createElement('div');
    overlay.id = 'authOverlay';
    overlay.innerHTML =
        '<div style="background:rgba(26,26,46,0.98);position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;font-family:Inter,-apple-system,sans-serif;">' +
            '<div style="background:#1e1e36;border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:40px;max-width:360px;width:90%;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.5);">' +
                '<div style="font-size:48px;margin-bottom:16px;">🔒</div>' +
                '<div style="color:#fff;font-size:20px;font-weight:700;margin-bottom:6px;">Dostęp chroniony</div>' +
                '<div style="color:#888;font-size:13px;margin-bottom:24px;">Wpisz hasło, aby kontynuować</div>' +
                '<input id="authInput" type="password" placeholder="Hasło" style="width:100%;padding:14px;background:#0f0f1a;border:2px solid rgba(255,255,255,0.12);border-radius:12px;color:#fff;font-size:16px;font-family:inherit;text-align:center;outline:none;transition:border-color 0.2s;" />' +
                '<div id="authError" style="color:#e8546a;font-size:12px;margin-top:10px;min-height:18px;"></div>' +
                '<button id="authBtn" style="width:100%;padding:14px;border:none;border-radius:12px;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;margin-top:8px;background:linear-gradient(135deg,#c41e3a,#d4234a);color:#fff;transition:transform 0.1s;">Wejdź</button>' +
            '</div>' +
        '</div>';

    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    var input = document.getElementById('authInput');
    var btn = document.getElementById('authBtn');
    var err = document.getElementById('authError');

    function tryAuth() {
        if (input.value === 'BKIHACK2026!') {
            sessionStorage.setItem('bki_auth', '1');
            if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
                window.location.href = '/jak-to-dziala.html';
                return;
            }
            overlay.remove();
            document.body.style.overflow = '';
        } else {
            err.textContent = 'Nieprawidłowe hasło';
            input.style.borderColor = '#c41e3a';
            input.value = '';
            setTimeout(function() { input.style.borderColor = 'rgba(255,255,255,0.12)'; }, 1500);
        }
    }

    btn.addEventListener('click', tryAuth);
    input.addEventListener('keydown', function(e) { if (e.key === 'Enter') tryAuth(); });
    setTimeout(function() { input.focus(); }, 100);
})();
