// script.js — FakeShield frontend interactions

// ── Character counter ──────────────────────────────────────────────────────
const textarea = document.getElementById('news_text');
const charCount = document.getElementById('charCount');

if (textarea && charCount) {
  const update = () => {
    const len = textarea.value.length;
    charCount.textContent = len;
    charCount.style.color = len < 20 ? '#ff4560' : len > 800 ? '#f0c040' : '#6b7280';
  };
  textarea.addEventListener('input', update);
  update();
}

// ── Submit button loading state ────────────────────────────────────────────
const form      = document.getElementById('analyzeForm');
const submitBtn = document.getElementById('submitBtn');

if (form && submitBtn) {
  form.addEventListener('submit', () => {
    submitBtn.querySelector('.btn-text').style.display    = 'none';
    submitBtn.querySelector('.btn-loading').style.display = 'inline';
    submitBtn.disabled = true;
  });
}

// ── Modal helpers ──────────────────────────────────────────────────────────
function toggleModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  const isHidden = modal.style.display === 'none' || !modal.style.display;
  modal.style.display = isHidden ? 'flex' : 'none';
  document.body.style.overflow = isHidden ? 'hidden' : '';
}

function switchModal(fromId, toId) {
  document.getElementById(fromId).style.display = 'none';
  document.getElementById(toId).style.display   = 'flex';
}

// Close modal on backdrop click
document.querySelectorAll('.modal').forEach(modal => {
  modal.addEventListener('click', e => {
    if (e.target === modal) {
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }
  });
});

// ── History filter buttons ─────────────────────────────────────────────────
const filterBtns = document.querySelectorAll('.filter-btn');
const historyItems = document.querySelectorAll('.history-item');

filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const filter = btn.dataset.filter;
    historyItems.forEach(item => {
      const show = filter === 'all' || item.dataset.label === filter;
      item.style.display = show ? '' : 'none';
    });
  });
});

// ── Auto-dismiss flash messages ────────────────────────────────────────────
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity .5s';
    el.style.opacity    = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);

// ── Risk meter animation on result page ────────────────────────────────────
const thumb = document.querySelector('.risk-thumb');
if (thumb) {
  const finalLeft = thumb.style.left;
  thumb.style.left = '0';
  requestAnimationFrame(() => {
    thumb.style.transition = 'left .8s cubic-bezier(.4,0,.2,1)';
    thumb.style.left = finalLeft;
  });
}
