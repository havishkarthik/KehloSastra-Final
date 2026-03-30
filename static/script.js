/**
 * Kehlosastra – Frontend JavaScript
 * Handles client-side validation and small UX enhancements.
 */

// ─── Auto-dismiss flash messages after 5 seconds ───────────────────────────
(function autoFlash() {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity .4s';
            el.style.opacity    = '0';
            setTimeout(function () { el.remove(); }, 400);
        }, 5000);
    });
})();

// ─── Set min date to today for the date picker on the create-game form ──────
(function setMinDate() {
    const dateInput = document.getElementById('date');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
    }
})();

// ─── Live player-count validation ──────────────────────────────────────────
(function validatePlayerCounts() {
    const totalInput   = document.getElementById('total_players');
    const withCreator  = document.getElementById('players_with_creator');

    if (!totalInput || !withCreator) return;

    function validate() {
        const total   = parseInt(totalInput.value,   10) || 0;
        const withMe  = parseInt(withCreator.value,  10) || 0;

        if (withMe >= total) {
            withCreator.setCustomValidity(
                '"Players Already With You" must be less than "Total Players Required".'
            );
        } else {
            withCreator.setCustomValidity('');
        }
    }

    totalInput.addEventListener('input',  validate);
    withCreator.addEventListener('input', validate);
})();

// ─── @sastra.ac.in email hint ───────────────────────────────────────────────
(function emailHint() {
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function (input) {
        input.addEventListener('blur', function () {
            const val = input.value.trim().toLowerCase();
            if (val && !val.endsWith('@sastra.ac.in')) {
                input.setCustomValidity('Only @sastra.ac.in email addresses are accepted.');
                input.reportValidity();
            } else {
                input.setCustomValidity('');
            }
        });
        input.addEventListener('input', function () {
            input.setCustomValidity('');
        });
    });
})();

// ─── Join-game double-submit guard ─────────────────────────────────────────
(function joinGuard() {
    const forms = document.querySelectorAll('form[action*="/join/"]');
    forms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled    = true;
                btn.textContent = 'Joining…';
            }
        });
    });
})();
