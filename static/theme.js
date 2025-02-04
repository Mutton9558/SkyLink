  function applyTheme() {
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      document.body.classList.add("dark-mode");
      document.body.classList.remove("light-mode");
      console.log("Dark mode applied");
    } else if (theme === "light") {
      document.body.classList.add("light-mode");
      document.body.classList.remove("dark-mode");
      console.log("Light mode applied");
    } else {
      applyAutoTheme();
    }
  }
  
  function applyAutoTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.body.classList.add("dark-mode");
      document.body.classList.remove("light-mode");
      console.log("Auto dark mode applied");
    } else {
      document.body.classList.add("light-mode");
      document.body.classList.remove("dark-mode");
      console.log("Auto light mode applied");
    }
  }
  
  document.addEventListener("DOMContentLoaded", applyTheme);