MSG = document.querySelector(".wait-msg");

// Toggle dropdown visibility when the profile button is clicked
document.querySelector(".profile").addEventListener("click", function (event) {
  event.stopPropagation(); // Prevent click from propagating to the document
  const dropdown = this.querySelector(".dropdown");
  dropdown.style.display =
    dropdown.style.display === "block" ? "none" : "block";
});

// Hide the dropdown when clicking outside
document.addEventListener("click", function () {
  const dropdown = document.querySelector(".dropdown");
  if (dropdown) {
    dropdown.style.display = "none";
  }
});

document.addEventListener("DOMContentLoaded", () => {
  // For Carousel Picture
  const carousel = document.querySelector(".carousel-images");
  const images = document.querySelectorAll(".carousel-images img");
  const prevButton = document.querySelector(".prev");
  const nextButton = document.querySelector(".next");

  // Update the carousel position
  function updateCarousel() {
    const offset = -currentIndex * 100; // Move the carousel by 100% per image
    carousel.style.transform = `translateX(${offset}%)`;
  }

  let currentIndex = 0;
  // Move to the previous image
  prevButton.addEventListener("click", () => {
    currentIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
    updateCarousel();
  });

  // Move to the next image
  nextButton.addEventListener("click", () => {
    currentIndex = currentIndex === images.length - 1 ? 0 : currentIndex + 1;
    updateCarousel();
  });

  //For hide and show the return date for round-trip and add stops for multi-city
  const form = document.querySelector("form");
  const tripOptions = document.querySelectorAll('input[name="trip"]');
  const passengerSelect = document.querySelector("select");
  const returnElement = document.querySelector(".return");
  const stopsElement = document.querySelector(".add-stops-button");
  const departureElement = document.querySelector(".departure");
  const bookingElement = document.querySelector(".booking-form");

  // Function to update visibility of the return element based on selected trip type
  function updatereturnVisibility() {
    const tripType = [...tripOptions].find(
      (option) => option.checked
    ).className;
    console.log(tripType);

    if (tripType === "one-trip") {
      returnElement.style.display = "none"; // Hide return for one-way
      stopsElement.style.display = "none";
      departureElement.style.margin = "0 3rem 0 3rem";
      bookingElement.style.margin = "0 10% 0 7.5%";
    } else if (tripType === "round-trip") {
      returnElement.style.display = "block"; // Show return for round trip
      stopsElement.style.display = "none";
      departureElement.style.margin = "0";
      bookingElement.style.margin = "0 10% 0 6%";
    } else {
      returnElement.style.display = "none";
      stopsElement.style.display = "block";
      departureElement.style.margin = "0 3rem 0 3rem";
      bookingElement.style.margin = "0 10% 0 6%";
    }
  }

  // Initial call to set the correct visibility based on the default selected trip type
  updatereturnVisibility();

  // Add event listeners to trip options to update visibility when changed
  tripOptions.forEach((option) => {
    option.addEventListener("change", updatereturnVisibility);
  });

  // Handle form submission
  form.addEventListener("submit", (e) => {
    e.preventDefault(); // Prevent actual form submission

    // Collect form data
    const tripType = [...tripOptions]
      .find((option) => option.checked)
      .nextSibling.textContent.trim();
    const from = form.querySelector('input[placeholder="From"]').value;
    const to = form.querySelector('input[placeholder="To"]').value;
    const departure = form.querySelector(
      'input[placeholder="Departure"]'
    ).value;
    const returnDate = form.querySelector('input[placeholder="Return"]').value;
    const passengers = passengerSelect.value;
    const promoCode = form.querySelector(
      'input[placeholder="Add promo code"]'
    ).value;

    // Simulate action or display collected data
    console.log({
      tripType,
      from,
      to,
      departure,
      returnDate,
      passengers,
      promoCode,
    });

    alert(`Flight search submitted for:
    - Trip type: ${tripType}
    - From: ${from}
    - To: ${to}
    - Departure: ${departure}
    - Return: ${returnDate}
    - Passengers/Class: ${passengers}
    - Promo code: ${promoCode ? promoCode : "None"}`);
  });
});

document.addEventListener("DOMContentLoaded", () => {});

function displayLoadMsg() {
  MSG.innerHTML =
    "Your inquiry may take a while to be submitted...Please be patient.";
}
