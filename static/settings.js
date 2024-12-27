document.addEventListener("DOMContentLoaded", function () {
  const editProfileBtn = document.getElementById("edit-profile-button");
  const changePasswordBtn = document.getElementById("change-password-button");
  const preferencesBtn = document.getElementById("preferences-button");

  const editProfileDivider = document.querySelector(".edit-profile");
  const changePasswordDivider = document.querySelector(".change-password");
  const preferencesDivider = document.querySelector(".preferences");

  // Initially display edit profile section and hide others
  editProfileDivider.style.display = "flex";
  changePasswordDivider.style.display = "none";
  preferencesDivider.style.display = "none";

  function hideAllDividers() {
    editProfileDivider.style.display = "none";
    changePasswordDivider.style.display = "none";
    preferencesDivider.style.display = "none";
  }

  editProfileBtn.addEventListener("click", function () {
    hideAllDividers();
    editProfileDivider.style.display = "flex";
  });

  changePasswordBtn.addEventListener("click", function () {
    hideAllDividers();
    changePasswordDivider.style.display = "flex";
  });

  preferencesBtn.addEventListener("click", function () {
    hideAllDividers();
    preferencesDivider.style.display = "flex";
  });

  darkModeToggle = document.getElementById("dark-mode-toggle");
  lightModeToggle = document.getElementById("light-mode-toggle");

  darkModeToggle.addEventListener("change", function () {
    if (darkModeToggle.checked) {
      document.body.classList.add("dark-mode");
      document.body.classList.remove("light-mode");
      localStorage.setItem("theme", "dark");
    }
  });

  lightModeToggle.addEventListener("change", function () {
    if (lightModeToggle.checked) {
      document.body.classList.add("light-mode");
      document.body.classList.remove("dark-mode");
      localStorage.setItem("theme", "light");
    }
  });

  const theme = localStorage.getItem("theme");
  if (theme === "dark") {
    darkModeToggle.checked = true;
    document.body.classList.add("dark-mode");
  } else if (theme === "light") {
    lightModeToggle.checked = true;
    document.body.classList.add("light-mode");
  }
});
