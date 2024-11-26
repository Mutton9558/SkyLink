document.querySelector('.profile').addEventListener('click', function() {
  const dropdown = this.querySelector('.dropdown');
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
});