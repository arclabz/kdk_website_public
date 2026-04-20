// KDK Website

/* === EVENT-BANNER (01.05.–03.05.2026) === */
(function () {
  const dev   = new URLSearchParams(window.location.search).has('dev');
  const now   = new Date();
  const start = new Date('2026-05-01');
  const end   = new Date('2026-05-04');
  if (dev || (now >= start && now < end)) {
    document.getElementById('event-banner').style.display = 'flex';
  }
})();

/* === SCROLL FADE-IN === */
const fadeEls = document.querySelectorAll('.section');
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); }
  });
}, { threshold: 0.1 });
fadeEls.forEach(el => observer.observe(el));

/* === KARTEN 3D-TILT === */
function applyTilt(cards) {
  cards.forEach(card => {
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width  - 0.5;
      const y = (e.clientY - r.top)  / r.height - 0.5;
      card.style.transform = `perspective(600px) rotateY(${x * 20}deg) rotateX(${-y * 20}deg) scale(1.08)`;
    });
    card.addEventListener('mouseleave', () => { card.style.transform = ''; });
  });
}
applyTilt(document.querySelectorAll('.hero-card'));
applyTilt(document.querySelectorAll('.split-cards img'));
