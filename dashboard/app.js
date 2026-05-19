'use strict';

/* ============================================
   Dye DAM Dashboard — Interactive Logic
   ============================================ */

const TOTAL_STEPS = 8;
let currentStep = 1;
let completedSteps = new Set();
let autoPlayInterval = null;
let isPlaying = false;

/* ---------- DOM refs ---------- */
const progressFill   = document.getElementById('progress-fill');
const progressBar    = document.getElementById('progress-bar');
const labelCurrent   = document.getElementById('current-step');
const labelTotal     = document.getElementById('total-steps');
const btnPrev        = document.getElementById('btn-prev');
const btnNext        = document.getElementById('btn-next');
const btnPlay        = document.getElementById('btn-play');
const playIcon       = document.getElementById('play-icon');
const navBtns        = document.querySelectorAll('.nav-btn');
const sections       = document.querySelectorAll('.guide-section');
const stepCards      = document.querySelectorAll('.step-card');
const completeBtns   = document.querySelectorAll('.complete-btn');

/* ============================================
   NAVIGATION (sections)
   ============================================ */
navBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.section;
    navBtns.forEach(b => { b.classList.remove('active'); b.setAttribute('aria-pressed', 'false'); });
    btn.classList.add('active');
    btn.setAttribute('aria-pressed', 'true');

    sections.forEach(s => s.classList.remove('active'));
    const section = document.getElementById(`section-${target}`);
    if (section) section.classList.add('active');

    /* show/hide toolbar only for demontage */
    document.querySelector('.toolbar').style.display = (target === 'demontage') ? '' : 'none';
  });
});

/* ============================================
   STEP NAVIGATION (toolbar)
   ============================================ */
function goToStep(n) {
  n = Math.max(1, Math.min(TOTAL_STEPS, n));
  currentStep = n;

  /* update cards */
  stepCards.forEach((card, idx) => {
    const stepNum = idx + 1;
    card.classList.toggle('active', stepNum === n);
    if (stepNum === n) {
      card.classList.add('highlight');
      setTimeout(() => card.classList.remove('highlight'), 700);
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  /* update progress */
  const pct = (n / TOTAL_STEPS) * 100;
  progressFill.style.width = `${pct}%`;
  progressBar.setAttribute('aria-valuenow', n);
  labelCurrent.textContent = n;

  /* update nav buttons */
  btnPrev.disabled = (n === 1);
  btnNext.disabled = (n === TOTAL_STEPS);
}

btnPrev.addEventListener('click', () => goToStep(currentStep - 1));
btnNext.addEventListener('click', () => goToStep(currentStep + 1));

/* ============================================
   AUTO PLAY
   ============================================ */
const PAUSE_SVG = '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>';

function startAutoPlay() {
  isPlaying = true;
  btnPlay.classList.add('playing');
  btnPlay.setAttribute('aria-pressed', 'true');
  btnPlay.setAttribute('aria-label', 'Pause lecture automatique');
  playIcon.innerHTML = PAUSE_SVG;

  autoPlayInterval = setInterval(() => {
    if (currentStep < TOTAL_STEPS) {
      goToStep(currentStep + 1);
    } else {
      stopAutoPlay();
    }
  }, 4000);
}

function stopAutoPlay() {
  isPlaying = false;
  clearInterval(autoPlayInterval);
  autoPlayInterval = null;
  btnPlay.classList.remove('playing');
  btnPlay.setAttribute('aria-pressed', 'false');
  btnPlay.setAttribute('aria-label', 'Lecture automatique');
  playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"/>';
}

btnPlay.addEventListener('click', () => {
  if (isPlaying) stopAutoPlay();
  else startAutoPlay();
});

/* ============================================
   STEP COMPLETION
   ============================================ */
completeBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const stepNum = parseInt(btn.dataset.step);
    const card = btn.closest('.step-card');

    if (completedSteps.has(stepNum)) {
      completedSteps.delete(stepNum);
      card.classList.remove('completed');
      btn.setAttribute('aria-label', `Marquer l'étape ${stepNum} comme complétée`);
      announceToScreenReader(`Étape ${stepNum} marquée comme non complétée.`);
    } else {
      completedSteps.add(stepNum);
      card.classList.add('completed');
      btn.setAttribute('aria-label', `Étape ${stepNum} complétée — cliquer pour annuler`);
      announceToScreenReader(`Étape ${stepNum} validée ! ${completedSteps.size} étape(s) sur ${TOTAL_STEPS} complétée(s).`);

      /* auto advance after short delay */
      if (stepNum === currentStep && currentStep < TOTAL_STEPS) {
        setTimeout(() => goToStep(currentStep + 1), 500);
      }
    }

    updateCompletionSummary();
  });
});

/* ============================================
   COMPLETION SUMMARY
   ============================================ */
function updateCompletionSummary() {
  const all = completedSteps.size === TOTAL_STEPS;
  if (all && !document.getElementById('completion-banner')) {
    const banner = document.createElement('div');
    banner.id = 'completion-banner';
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');
    banner.innerHTML = `
      <div class="completion-banner">
        <span class="comp-icon" aria-hidden="true">🎉</span>
        <div>
          <strong>Démontage complet !</strong>
          <p>Toutes les étapes ont été validées. Votre Dye DAM est prêt pour le nettoyage et le remontage.</p>
        </div>
        <button onclick="this.parentElement.parentElement.remove()" aria-label="Fermer la notification">✕</button>
      </div>
    `;
    document.querySelector('.guide-section.active').prepend(banner);

    injectBannerStyle();
  }
}

function injectBannerStyle() {
  if (document.getElementById('banner-style')) return;
  const style = document.createElement('style');
  style.id = 'banner-style';
  style.textContent = `
    .completion-banner {
      display: flex; align-items: center; gap: 1rem;
      background: rgba(6,214,160,.12); border: 1px solid rgba(6,214,160,.4);
      border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;
    }
    .comp-icon { font-size: 2rem; flex-shrink: 0; }
    .completion-banner strong { color: #06d6a0; font-size: 1rem; }
    .completion-banner p { font-size: .85rem; color: #c8d3e6; margin-top: .2rem; }
    .completion-banner button {
      margin-left: auto; background: none; border: none; cursor: pointer;
      color: #6b7a9e; font-size: 1.1rem; padding: .25rem;
      flex-shrink: 0;
    }
    .completion-banner button:hover { color: #c8d3e6; }
  `;
  document.head.appendChild(style);
}

/* ============================================
   SCREEN READER ANNOUNCEMENTS
   ============================================ */
function announceToScreenReader(msg) {
  let live = document.getElementById('sr-announce');
  if (!live) {
    live = document.createElement('div');
    live.id = 'sr-announce';
    live.setAttribute('aria-live', 'polite');
    live.setAttribute('aria-atomic', 'true');
    live.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;';
    document.body.appendChild(live);
  }
  live.textContent = '';
  requestAnimationFrame(() => { live.textContent = msg; });
}

/* ============================================
   KEYBOARD SHORTCUTS
   ============================================ */
document.addEventListener('keydown', e => {
  /* Ignore when typing in inputs */
  if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(e.target.tagName)) return;

  switch (e.key) {
    case 'ArrowRight':
    case 'ArrowDown':
      e.preventDefault();
      goToStep(currentStep + 1);
      break;
    case 'ArrowLeft':
    case 'ArrowUp':
      e.preventDefault();
      goToStep(currentStep - 1);
      break;
    case ' ':
      e.preventDefault();
      if (isPlaying) stopAutoPlay(); else startAutoPlay();
      break;
    case '1': case '2': case '3': case '4':
    case '5': case '6': case '7': case '8':
      goToStep(parseInt(e.key));
      break;
  }
});

/* ============================================
   STEP CARD CLICK (direct navigation)
   ============================================ */
stepCards.forEach((card, idx) => {
  card.addEventListener('click', e => {
    if (e.target.closest('.complete-btn')) return;
    goToStep(idx + 1);
  });
  card.style.cursor = 'pointer';
});

/* ============================================
   INIT
   ============================================ */
function init() {
  labelTotal.textContent = TOTAL_STEPS;
  goToStep(1);

  /* Keyboard shortcut hint */
  const hint = document.createElement('p');
  hint.style.cssText = 'text-align:center;font-size:.72rem;color:#3d4a6b;margin-top:1rem;';
  hint.setAttribute('aria-hidden', 'true');
  hint.textContent = 'Raccourcis : ← → pour naviguer · Espace pour lecture auto · Touches 1–8 pour aller à une étape';
  document.querySelector('.toolbar-inner').appendChild(hint);
}

document.addEventListener('DOMContentLoaded', init);
