/* ============================================================
   KehloSastra – Frontend JS
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  // -----------------------------------------------------------------------
  // Navbar: scroll shadow + mobile toggle
  // -----------------------------------------------------------------------
  const navbar    = document.getElementById('navbar');
  const navToggle = document.getElementById('navToggle');
  const navLinks  = document.getElementById('navLinks');

  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 20);
  });

  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const expanded = navLinks.classList.contains('open');
    navToggle.setAttribute('aria-expanded', expanded);
  });

  // Close mobile nav when a link is clicked
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => navLinks.classList.remove('open'));
  });

  // -----------------------------------------------------------------------
  // Set date inputs to today as minimum
  // -----------------------------------------------------------------------
  const today = new Date().toISOString().split('T')[0];
  const dateInput     = document.getElementById('date');
  const availDateInput = document.getElementById('avail_date');

  if (dateInput)     dateInput.min = today;
  if (availDateInput) availDateInput.min = today;

  // -----------------------------------------------------------------------
  // Booking form
  // -----------------------------------------------------------------------
  const bookingForm    = document.getElementById('bookingForm');
  const submitBtn      = document.getElementById('submitBtn');
  const btnText        = submitBtn.querySelector('.btn-text');
  const btnSpinner     = submitBtn.querySelector('.btn-spinner');
  const formMessage    = document.getElementById('formMessage');

  // Cache form inputs to avoid repeated DOM queries on each submit
  const nameInput      = document.getElementById('name');
  const sportSelect    = document.getElementById('sport');
  const startTimeInput = document.getElementById('start_time');
  const endTimeInput   = document.getElementById('end_time');

  function showMessage(text, type) {
    formMessage.textContent = text;
    formMessage.className   = `form-message show ${type}`;
  }

  function clearMessage() {
    formMessage.className   = 'form-message';
    formMessage.textContent = '';
  }

  function setLoading(loading) {
    submitBtn.disabled    = loading;
    btnText.hidden        = loading;
    btnSpinner.hidden     = !loading;
  }

  bookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMessage();

    const name       = nameInput.value.trim();
    const sport      = sportSelect.value;
    const date       = dateInput.value;
    const start_time = startTimeInput.value;
    const end_time   = endTimeInput.value;

    // Client-side quick checks
    if (!name || !sport || !date || !start_time || !end_time) {
      showMessage('Please fill in all fields.', 'error');
      return;
    }

    if (end_time <= start_time) {
      showMessage('End time must be after start time.', 'error');
      return;
    }

    setLoading(true);

    try {
      const res  = await fetch('/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, sport, date, start_time, end_time }),
      });

      const data = await res.json();

      if (data.success) {
        showMessage(`✅ ${data.message}`, 'success');
        bookingForm.reset();
        if (dateInput) dateInput.min = today;
      } else {
        showMessage(`❌ ${data.error}`, 'error');
      }
    } catch {
      showMessage('Network error. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  });

  // Auto-clear message after 6 s
  formMessage.addEventListener('transitionend', () => {
    if (formMessage.classList.contains('show')) {
      setTimeout(() => clearMessage(), 6000);
    }
  });

  // -----------------------------------------------------------------------
  // Availability checker
  // -----------------------------------------------------------------------
  const checkAvailBtn    = document.getElementById('checkAvailBtn');
  const availResults     = document.getElementById('availResults');
  const availSportSelect = document.getElementById('avail_sport');

  checkAvailBtn.addEventListener('click', async () => {
    const sport = availSportSelect.value;
    const date  = availDateInput.value;

    if (!sport || !date) {
      availResults.innerHTML = '<p class="avail-empty">Please select both a sport and a date.</p>';
      return;
    }

    checkAvailBtn.disabled    = true;
    checkAvailBtn.textContent = 'Checking…';
    availResults.innerHTML    = '';

    try {
      const res  = await fetch(`/availability?sport=${encodeURIComponent(sport)}&date=${encodeURIComponent(date)}`);
      const data = await res.json();

      if (!res.ok) {
        availResults.innerHTML = `<p class="avail-empty">${data.error || 'Error fetching availability.'}</p>`;
        return;
      }

      if (data.bookings.length === 0) {
        availResults.innerHTML = '<div class="avail-all-free">✅ No bookings yet — all slots are free!</div>';
      } else {
        const sportLabel = sport.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        let html = `<p style="font-size:.82rem;color:var(--text-muted);margin-bottom:10px;">${data.bookings.length} booking(s) found for <strong>${sportLabel}</strong> on <strong>${date}</strong>:</p>`;
        data.bookings.forEach(b => {
          html += `
            <div class="avail-slot">
              <span class="avail-slot-time">${b.start_time} – ${b.end_time}</span>
              <span class="avail-slot-name">${escapeHtml(b.name)}</span>
            </div>`;
        });
        availResults.innerHTML = html;
      }
    } catch {
      availResults.innerHTML = '<p class="avail-empty">Network error. Please try again.</p>';
    } finally {
      checkAvailBtn.disabled    = false;
      checkAvailBtn.textContent = 'Check Availability';
    }
  });

  // -----------------------------------------------------------------------
  // FAQ accordion
  // -----------------------------------------------------------------------
  const faqItems = document.querySelectorAll('.faq-item');

  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('open');

      // Close all using the cached list
      faqItems.forEach(i => i.classList.remove('open'));

      // Open current if it was closed
      if (!isOpen) item.classList.add('open');
    });
  });

  // -----------------------------------------------------------------------
  // Smooth scroll for anchor links (fallback for older browsers)
  // -----------------------------------------------------------------------
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = 80; // navbar height
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  // -----------------------------------------------------------------------
  // Helper
  // -----------------------------------------------------------------------
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

});
