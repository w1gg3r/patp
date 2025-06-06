// === Пагинация ===
const NEWS_PER_PAGE = 4;
let currentPage = 1;

function showPage(page) {
    currentPage = page;
    const container = document.getElementById('news-container');
    const pagination = document.getElementById('pagination');

    // Загружаем новости с сервера
    fetch(`/api/news?page=${page}`)
        .then(res => res.json())
        .then(data => {
            container.innerHTML = '';
            pagination.innerHTML = '';

            // Добавляем каждую новость
            for (let i = 0; i < NEWS_PER_PAGE; i++) {
                if (data.news[i]) {
                    const news = data.news[i];
                    container.innerHTML += `
                        <div class="news-card">
                            <img src="${news.image}" alt="${news.title}">
                            <div class="news-content">
                                <h3>${news.title}</h3>
                                <p>${news.description}</p>
                                <div class="news-footer">
                                    <a href="/single-news/${news.id}" class="news-btn">Подробнее</a>
                                    <p class="news-date">${news.date}</p>
                                </div>
                            </div>
                        </div>`;
                } else {
                    container.innerHTML += `<div class="news-card news-card-empty"></div>`;
                }
            }

            // Пагинация
            const totalPages = Math.ceil(data.total / data.per_page);
            for (let i = 1; i <= totalPages; i++) {
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = i;
                if (i === data.current_page) link.classList.add('active');
                link.onclick = () => {
                    showPage(i);
                    return false;
                };
                pagination.appendChild(link);
            }

        })
        .catch(err => {
            container.innerHTML = `<p>Ошибка при загрузке новостей.</p>`;
        });
}

// === Модальное окно ===
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "block";
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "none";
    }
}

// Закрытие модального окна по клику вне его
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
};

// === Инициализация ===
window.onload = () => {
    showPage(1); // Загрузить первую страницу новостей
};