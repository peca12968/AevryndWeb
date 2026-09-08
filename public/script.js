const buttons = [...document.querySelectorAll('.filters button')];
const milestones = [...document.querySelectorAll('.milestone')];

buttons.forEach((button) => {
  button.addEventListener('click', () => {
    const filter = button.dataset.filter;
    buttons.forEach((item) => {
      const selected = item === button;
      item.classList.toggle('active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    milestones.forEach((item) => {
      const categories = item.dataset.category.split(' ');
      item.classList.toggle('hidden', filter !== 'all' && !categories.includes(filter));
    });
  });
});
