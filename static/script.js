document.querySelector('.profile').addEventListener('click', function() {
  const dropdown = this.querySelector('.dropdown');
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
});

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const tripOptions = document.querySelectorAll('input[name="trip"]');
  const passengerSelect = document.querySelector('select');
  const returnElement = document.querySelector('.return');

  // Function to update visibility of the return element based on selected trip type
  function updatereturnVisibility() {
    const tripType = [...tripOptions].find(option => option.checked).value;

    if (tripType === 'one-way') {
      returnElement.style.display = 'none'; // Hide return for one-way
    } else {
      returnElement.style.display = 'block'; // Show return for round trip
    }
  }

  // Initial call to set the correct visibility based on the default selected trip type
  updatereturnVisibility();

  // Add event listeners to trip options to update visibility when changed
  tripOptions.forEach(option => {
    option.addEventListener('change', updatereturnVisibility);
  });

  // Handle form submission
  form.addEventListener('submit', (e) => {
    e.preventDefault(); // Prevent actual form submission

    // Collect form data
    const tripType = [...tripOptions].find(option => option.checked).nextSibling.textContent.trim();
    const from = form.querySelector('input[placeholder="From"]').value;
    const to = form.querySelector('input[placeholder="To"]').value;
    const departure = form.querySelector('input[placeholder="Departure"]').value;
    const returnDate = form.querySelector('input[placeholder="Return"]').value;
    const passengers = passengerSelect.value;
    const promoCode = form.querySelector('input[placeholder="Add promo code"]').value;

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
    - Promo code: ${promoCode ? promoCode : 'None'}`);
  });
});