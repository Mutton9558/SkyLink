let MSG = document.querySelector(".wait-msg");
let PASS_INPUT_BOX = document.querySelector("#login-pass");
let SHOW_PASSWORD_IMAGE = document.querySelector("#pass-img");

const carousel = document.querySelector(".carousel-images");
const images = document.querySelectorAll(".carousel-images img");
const prevButton = document.querySelector(".prev");
const nextButton = document.querySelector(".next");
let currentIndex = 0;
const form = document.querySelector("form");
const tripOptions = document.querySelectorAll('input[name="trip"]');
const passengerSelect = document.querySelector("select");
const returnElement = document.querySelector(".return");
const stopsElement = document.querySelector(".add-stops-button");
const departureElement = document.querySelector(".departure");
const addStopsButton = document.getElementById("addFlight");
const stopFieldsContainer = document.getElementById("container");
const departureInput = document.querySelector(".departureDate");
const returnInput = document.querySelector(".returnDate");
const today = new Date();
const year = today.getFullYear();
const month = String(today.getMonth() + 1).padStart(2, "0");
const day = String(today.getDate()).padStart(2, "0");
const formattedToday = `${year}-${month}-${day}`;

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

  // For hide and show the return date for round-trip and add stops for multi-city
  const form = document.querySelector("form");
  const tripOptions = document.querySelectorAll(".trip-class");
  const passengerSelect = document.querySelector("select");
  const returnElement = document.querySelector(".return");
  const stopsElement = document.querySelector(".add-stops-button");
  const departureElement = document.querySelector(".departure");
  const bookingElement = document.querySelector(".booking-form");

  // Update the carousel position
  function updateCarousel() {
    const offset = -currentIndex * 100; // Move the carousel by 100% per image
    carousel.style.transform = `translateX(${offset}%)`;
  }

  // Move to the previous image
  prevButton.addEventListener("click", () => {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    updateCarousel();
  });

  // Move to the next image
  nextButton.addEventListener("click", () => {
    currentIndex = (currentIndex + 1) % images.length;
    updateCarousel();
  });

  // Function to update visibility of the return element based on selected trip type
  function updateReturnVisibility() {
    const tripType = [...tripOptions].find((option) => option.checked).value;
    console.log(tripType);
    const newStops = document.querySelectorAll(".duplicateFields");
    const returnDateInput = returnElement.querySelector("input");
    switch (tripType) {
      case "one-way":
        returnElement.style.display = "none";
        returnDateInput.removeAttribute("required"); // Hide return for one-way
        stopsElement.style.display = "none";
        newStops.forEach((stopField) => {
          stopField.style.display = "none";
          const inputDuplicates = stopField.querySelectorAll("input, select");
          inputDuplicates.forEach((input) => {
            input.removeAttribute("required");
          });
        });
        departureElement.style.margin = "0 3rem 0 3rem";
        break;
      case "round-trip":
        returnElement.style.display = "block";
        returnDateInput.setAttribute("required", true); // Show return for round trip
        stopsElement.style.display = "none";
        newStops.forEach((stopField) => {
          stopField.style.display = "none";
          const inputDuplicates = stopField.querySelectorAll("input, select");
          inputDuplicates.forEach((input) => {
            input.removeAttribute("required");
          });
        });
        departureElement.style.margin = "0";
        break;
      default:
        returnElement.style.display = "none";
        returnDateInput.removeAttribute("required");
        stopsElement.style.display = "block";
        departureElement.style.margin = "0 3rem 0 3rem";
        newStops.forEach((stopField) => {
          stopField.style.display = "flex";
          const inputDuplicates = stopField.querySelectorAll("input, select");
          inputDuplicates.forEach((input) => {
            input.setAttribute("required", true);
          });
        });
      // firstStops.style.display = "flex";
    }
  }

  if (departureInput) {
    departureInput.setAttribute("min", formattedToday);
  }

  function updateReturnMinDate() {
    const departureDate = new Date(departureInput.value);

    if (!isNaN(departureDate.getTime())) {
      if (departureDate.toDateString() == today.toDateString()) {
        returnInput.setAttribute("min", formattedToday);
      } else {
        departureDate.setDate(departureDate.getDate() + 1);
        const year = departureDate.getFullYear();
        const month = String(departureDate.getMonth() + 1).padStart(2, "0");
        const day = String(departureDate.getDate()).padStart(2, "0");
        const formattedDate = `${year}-${month}-${day}`;

        returnInput.setAttribute("min", formattedDate);
      }
    } else {
      returnInput.removeAttribute("min");
    }
  }

  if (departureInput) {
    departureInput.addEventListener("change", updateReturnMinDate);
  }

  function setMinDateForAllDepartures() {
    const departureInputs = document.querySelectorAll(".departure-date-0");
    departureInputs.forEach((input) => {
      input.setAttribute("min", formattedToday);
    });
  }

  setMinDateForAllDepartures();

  // Initial call to set the correct visibility based on the default selected trip type
  updateReturnVisibility();

  // Add event listeners to trip options to update visibility when changed
  tripOptions.forEach((option) => {
    option.addEventListener("change", updateReturnVisibility);
  });

  const addStopsButton = document.getElementById("addFlight");
  const stopFieldsContainer = document.getElementById("container");

  let fieldCounter = 1;

  addStopsButton.addEventListener("click", () => {
    const currentStops =
      stopFieldsContainer.querySelectorAll(".duplicateFields").length;

    if (currentStops < 3) {
      // Find the first duplicateFlights element to clone
      const duplicateFlight =
        stopFieldsContainer.querySelector(".duplicateFields");

      if (duplicateFlight) {
        // Clone the duplicateFlights element
        const newFlight = duplicateFlight.cloneNode(true);

        // Update the name attributes of the cloned fields
        const selects = newFlight.querySelectorAll("select[name], input[name]");
        selects.forEach((select) => {
          const name = select.getAttribute("name");
          if (name) {
            // Append the counter value to the name
            select.setAttribute("name", `${name}${fieldCounter}`);
          }
        });

        // Append the cloned element to the container
        stopFieldsContainer.appendChild(newFlight);

        // Increment the counter
        fieldCounter++;

        const removeButton = document.createElement("button");
        removeButton.textContent = "X";
        removeButton.classList.add("remove-stop");
        removeButton.title = "Remove stop";

        removeButton.addEventListener("click", () => {
          stopFieldsContainer.removeChild(newFlight);
        });

        // Append the cloned element to the container
        stopFieldsContainer.appendChild(newFlight);

        newFlight.appendChild(removeButton);
      }
    } else {
      alert("You can't add more than 3 stops");
    }
  });

  // Handle form submission
  // form.addEventListener("submit", (e) => {
  //   e.preventDefault();

  // Collect form data
  // const tripType = [...tripOptions]
  //   .find((option) => option.checked)
  //   .nextSibling.textContent.trim();
  // const from = form.querySelector('input[placeholder="From"]').value;
  // const to = form.querySelector('input[placeholder="To"]').value;
  // const departure = form.querySelector(
  //   'input[placeholder="Departure"]'
  // ).value;
  // const returnDate = form.querySelector('input[placeholder="Return"]').value;
  // const passengers = passengerSelect.value;
  // const promoCode = form.querySelector(
  //   'input[placeholder="Add promo code"]'
  // ).value;

  // Simulate action or display collected data
  // console.log({
  //   tripType,
  //   from,
  //   to,
  //   departure,
  //   returnDate,
  //   passengers,
  //   promoCode,
  // });

  // alert(`Flight search submitted for:
  // - Trip type: ${tripType}
  // - From: ${from}
  // - To: ${to}
  // - Departure: ${departure}
  // - Return: ${returnDate}
  // - Passengers/Class: ${passengers}
  // - Promo code: ${promoCode ? promoCode : "None"}`);
  //   });
});

function displayLoadMsg() {
  MSG.innerHTML =
    "Your inquiry may take a while to be submitted...Please be patient.";
}

function showPassword() {
  if (PASS_INPUT_BOX.type == "text") {
    PASS_INPUT_BOX.type = "password";
    SHOW_PASSWORD_IMAGE.src =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAAXNSR0IArs4c6QAAA5VJREFUSEuVlk9oHVUUxn+HxLprYl6lilLEELcJFdqVqNBqSQu2zaaiFBFLu1AKWgLd60qoioIGUxSkzaJ/lNI/NBvNwkUWLqwUSy1i243YSpFkUVLwOGfmzMydmTtvnneR3Dnv3nvO+c53vnuFYAig/l3OBUFRN6T/yj/h9mIenpMaG4bMVHUVOmgEEfVTM7Z4yTMKzhws6kGCiPjsh2h7Gv/joG4sqoUMoI4iHi/QINl3RNJ0PMihIbkGJlpIUpu3sLoRsPAIyqvAM0AP2ODg3QX+Bq4DJ4B/OiqUEb17kTwr6KzCXpDhtOHaifsA5DToB8DVavCxGse9jwGfAK9Hsr+Dcst7dBPKozUNUIXjwLvASqzcbTUeAX4ApnzTGvAVcCG1CyuFomQLRgSeV9gFvAE8lJnlR0G3qXC/UKZYH3vUDwNLwFZfcxY4BNypRx5XOh7zIHf4+svANPCvI5RKXyzjBZB9Lp4fArPlhnQ27oFMCqwoLAJzNZKKCnMoB9z+kcNeLKs7fgv40tgj6DmF3WBnaI6UOV1G6NWgsxIYzGHfDwHfA89lZJRp0Eu558xxhtkocBNYnxDqBrA5q2UFYEPgSAtZDmktc0hh/8VaL6n9HwLj6pCHGb+d9OenfujLZBDWx6LA9spNVa44izBTDTTNyHr/pC/bn5TqmzzXfOth4GP/2JMw+ruK1wyVM6T9HB1GwpkIAWdUOO0BvYPwWS4FvlZGQX9LftiAchuYBO5V2KAcTOD7osWxMT8lWaCiBvGVxP44yJ+CTiis1jO27zBrI4IRJmuDcpwHdtYcBOTK82AIdXJlJmP4fDZtttM6hGWUKe/RY4nyvBd6dbtl/pLPy3YqG9tm5uRN37sE8iKYoOWum7g9AfwEbPQl3wp6UFMB6Vb2pB1t/9cI27yuvwNb/CKpVC5SMnkK1DKZ8B/XEOZRLqaqJqzW2sx0/QXgFeA1wHrYIP0ZdHtT9SRyO3lSAj0Fg9paoMIY4K8ERrskhpOAnkTTPg2H8eJz4Gj/S6I/gqbZdoARajhS79Bkl8kpgfcVrhWlaTwWKuTqqJ8whqZX5NOuRL3gIXBX4FeFhSLDErn6xVQAWPAs0ORI3eum+sWe63lnAsVbIiB47fHbF9eBGB6KSdlH9ogp4ffHWBhGtDbFTdWKSndI8fu4cWDDf0nz9pL09R57ZXaHG9GRCJO6Sl1VuXiN4xlXkx04Xl/4H2PqHTfQ11RTAAAAAElFTkSuQmCC";
  } else {
    PASS_INPUT_BOX.type = "text";
    SHOW_PASSWORD_IMAGE.src =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAAXNSR0IArs4c6QAAA/dJREFUSEuVl0uoVlUUx39LKxTKIs0iIsKoQRQNHEg0UCgwsps9QHtjVwxBQggnQjgRhz0GIkbeGpQGWXELswe9oaIIB4oQmSAVDXrebkWZXVdnnb3OOevsb58Lncn9zjp7r+f/v9a6QvERQMH/1Efq31EQRUPno/K+MnvrGxhxpKDUz4z4VY6i1R997xn2DwtQma4jdq8EbYPtjPWj72wWslJwKBnunkuBz4AtAnuzzA7pHsrRUPxtkpsDZwBHEa5ERUHvAl4cvi3UmZhV/VCNU/YjSsaBPSYRmFG4A3itfL1geCj7hZzkqbYjZnzCdcwAtwIHEc5GWStwnQpLUOYI/KXwE/Az8BWwF/itnAR3NGC1dG69R27fTgEvAGuAeUMscH2nQF4C3VGXrXkGqDhUpWg8PzMFHHehAfKCLMtW+gngEYHfO35ErgS3Im1cXBsPDlv9t1fl+Cbz5FxgOXALyLoq4jPTd/kY9Ebg79zzUOPW57nAUoHPnU51zV3RlKA3KBzqd4We2ouAZxFucvK/BdwMnI5lGm0gsBt4AFhVRfG+qwzGmULYhtaIN1C9BzwFGBAjRUy2we8/YWnP2RHfVyK86W36gMJYqMQ42kQeTKSfHwErUoNv2TkX5V2B5V5jC+RgxFvz21J8uGoaVwHfCVyjYCCKsyJFXkBpBbb7gef7SMbSfgRYVNX+BOjlTcojj2Mt7xV0XwmNDc/NnaxzPeclyv26G9jnDt3j1PTOlWqzCXSnJ/F2QSdH22ELwI5qXUPYr8Kadpp28gcVnnHDDwFPJ6e73Jwn6DGt08K3wLXAr1nqYnFznu9AeDRr3ucAXwOLQX4BvRg4WYeZjbnNwJNu7I3ES6dBTsT0Ho0bXe4EJh3cc1CZFHTMM7epcmBX43neq88CPjEeu53HbESWbbbScZAJ31hmUFYJvKNp2KzzU58C1zeozyJuFV1SRfoFcKFLXgE2Aj9mCI/+pMgT2k+C2n0zZKLjmqhmTAnrRbgePlwGvF1NmyucTP9QA0QOgH6I8Ee+knVod4VJ2QcCqxWm86yFGo8sbwuBxxuK9C4KP6B1v/4TsK70qn/vKJkMjwlYIxp5eoYHarmsQuJWb6G2peSPjc3VgIHRkrte0D1u7F/gNuD1vEylRaBTHIa2wvkVNe4DlngnWijofE2oP1b17YcBK4k9Ee3Ww9eCvBxX5lHD/2N96aBS3JDbNcopaTvc/iaqnuHI6a4dDnuSo7TQYmMb/hL06maKlebxLBt+f28aRUxkauQ5tgpZb/jecRBbZuE/lgG0NeNq1qpEfAgLUKbjUBtIdbTYR9iQL2X5LGXKenXL/sL+lcjSZrOgdMhOQf4fmThYMyvEgtMAAAAASUVORK5CYII=";
  }
}
