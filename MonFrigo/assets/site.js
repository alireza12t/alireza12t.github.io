// MonFrigo site: EN/FR toggle, mobile menu, shared footer.
(function () {
  const APP_STORE = "https://apps.apple.com/ca/app/monfrigo/id6808321210";
  const root = document.documentElement;

  // Language: saved choice, else the browser's, else English
  let saved = null;
  try { saved = localStorage.getItem("monfrigo-lang"); } catch (e) {}
  const initial = saved || ((navigator.language || "").toLowerCase().startsWith("fr") ? "fr" : "en");
  setLang(initial);

  function setLang(lang) {
    root.lang = lang;
    document.querySelectorAll("[data-lang-toggle]").forEach(a => {
      a.textContent = lang === "fr" ? "English" : "Français";
      a.setAttribute("lang", lang === "fr" ? "en" : "fr");
    });
  }

  document.addEventListener("click", e => {
    const toggle = e.target.closest("[data-lang-toggle]");
    if (toggle) {
      e.preventDefault();
      const next = root.lang === "fr" ? "en" : "fr";
      try { localStorage.setItem("monfrigo-lang", next); } catch (err) {}
      setLang(next);
    }
    const menu = e.target.closest("[data-menu]");
    if (menu) {
      const nav = document.querySelector("[data-nav]");
      const open = nav.classList.toggle("open");
      menu.setAttribute("aria-expanded", open);
    }
  });

  document.querySelectorAll("[data-link=appStore]").forEach(a => {
    a.href = APP_STORE;
    a.target = "_blank";
    a.rel = "noopener";
  });

  const footer = document.querySelector("[data-footer]");
  if (footer) {
    footer.innerHTML = `
      <div class="wrap">
        <div class="foot-grid">
          <div>
            <div class="foot-brand"><img src="assets/icon.webp" alt="" width="40" height="40"><span>MonFrigo</span></div>
            <p class="only-en">Track your fridge, waste less food.</p>
            <p class="only-fr">Suivez votre frigo, gaspillez moins.</p>
          </div>
          <div>
            <h4><span class="only-en">App</span><span class="only-fr">L’app</span></h4>
            <ul>
              <li><a href="index.html#features"><span class="only-en">Features</span><span class="only-fr">Fonctionnalités</span></a></li>
              <li><a href="index.html#screens"><span class="only-en">Screenshots</span><span class="only-fr">Captures</span></a></li>
              <li><a href="${APP_STORE}" target="_blank" rel="noopener">App Store</a></li>
            </ul>
          </div>
          <div>
            <h4><span class="only-en">Help</span><span class="only-fr">Aide</span></h4>
            <ul>
              <li><a href="support.html"><span class="only-en">Support</span><span class="only-fr">Assistance</span></a></li>
              <li><a href="privacy.html"><span class="only-en">Privacy</span><span class="only-fr">Confidentialité</span></a></li>
              <li><a href="../"><span class="only-en">About the developer</span><span class="only-fr">Le développeur</span></a></li>
            </ul>
          </div>
        </div>
        <div class="foot-bottom">
          <span>© ${new Date().getFullYear()} Alireza Toghiani Khorasgani</span>
          <span class="only-en">Made in Canada</span><span class="only-fr">Fait au Canada</span>
        </div>
      </div>`;
  }
})();
