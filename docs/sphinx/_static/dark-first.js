// Dark first (brand.toml [theme.docs] scheme = "dark"): unless the reader has picked a theme with Furo's
// toggle, start in dark. Furo stores the choice in localStorage under "theme".
(function () {
  try {
    if (!localStorage.getItem("theme")) {
      localStorage.setItem("theme", "dark");
      document.body.dataset.theme = "dark";
    }
  } catch (e) {
    // storage blocked: Furo's default (follow the system) applies
  }
})();
