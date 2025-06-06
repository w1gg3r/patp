function showForm(formType) {
    const orderForm = document.getElementById('order-form');
    const jobForm = document.getElementById('job-form');
    const buttons = document.querySelectorAll('.tab-btn');

    if (formType === 'order') {
        orderForm.style.display = 'block';
        jobForm.style.display = 'none';
        buttons[0].classList.add('active');
        buttons[1].classList.remove('active');
    } else {
        orderForm.style.display = 'none';
        jobForm.style.display = 'block';
        buttons[0].classList.remove('active');
        buttons[1].classList.add('active');
    }
}