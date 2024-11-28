document.querySelector('.profile').addEventListener('click', function() {
  const dropdown = this.querySelector('.dropdown');
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
});

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const tripOptions = document.querySelectorAll('input[name="trip"]');
  const passengerSelect = document.querySelector('select');
  
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