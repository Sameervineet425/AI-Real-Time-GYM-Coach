// Live Streamlit deployment of the coach. VITE_APP_URL can override it if the app moves.
const APP_URL = import.meta.env.VITE_APP_URL || 'https://ai--coach.streamlit.app/'

for (const link of document.querySelectorAll('[data-app-link]')) {
  link.href = APP_URL
  link.target = '_blank'
  link.rel = 'noopener'
}

// Animate the HUD readouts to simulate a live squat set.
const knee = document.getElementById('knee')
const reps = document.getElementById('reps')
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

if (knee && reps && !reduceMotion) {
  let t = 0
  let count = 7
  let wasDown = false
  setInterval(() => {
    t += 0.08
    const angle = Math.round(131 + 41 * Math.cos(t)) // 90°–172°
    knee.textContent = `${angle}°`
    const down = angle < 100
    if (wasDown && !down) {
      count = count >= 12 ? 1 : count + 1
      reps.textContent = String(count).padStart(2, '0')
    }
    wasDown = down
  }, 60)
}
