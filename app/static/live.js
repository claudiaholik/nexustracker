// Cuenta atrás del temporizador de ronda y recarga automática cada 30 s.
(function () {
  const timer = document.querySelector(".timer");
  if (timer) {
    let seconds = parseInt(timer.dataset.seconds, 10);
    const running = timer.dataset.running === "true";
    const value = timer.querySelector(".timer-value");
    const paint = () => {
      const m = Math.floor(seconds / 60), s = seconds % 60;
      value.textContent = `${m}:${String(s).padStart(2, "0")}`;
      timer.classList.toggle("low", seconds <= 300);
    };
    paint();
    if (running) setInterval(() => { if (seconds > 0) { seconds--; paint(); } }, 1000);
  }

  // No recargamos si la persona está escribiendo en el buscador.
  setInterval(() => {
    if (document.activeElement && document.activeElement.tagName === "INPUT") return;
    location.reload();
  }, 30000);
})();
