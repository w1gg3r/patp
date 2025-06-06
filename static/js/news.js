const NEWS_PER_PAGE = 4;
let currentPage = 1;
let newsList = [];

async function loadNews() {
    try {
        const response = await fetch('/api/news/all');
        const data = await response.json();
        newsList = data; // Убедитесь, что данные передаются корректно
        showPage(currentPage);
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('news-container').innerHTML = '<p>Не удалось загрузить новости</p>';
    }
}

function showPage(page) {
    const container = document.getElementById('news-container');
    const pagination = document.getElementById('news-pagination');

    container.innerHTML = '';
    pagination.innerHTML = '';

    const start = (page - 1) * NEWS_PER_PAGE;
    const end = start + NEWS_PER_PAGE;
    const newsToShow = newsList.slice(start, end);

    if (newsToShow.length === 0) {
        container.innerHTML = '<p>Нет новостей</p>';
        return;
    }

    newsToShow.forEach(news => {
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
            </div>
        `;
    });

    const totalPages = Math.ceil(newsList.length / NEWS_PER_PAGE);
    for (let i = 1; i <= totalPages; i++) {
        const link = document.createElement('a');
        link.href = '#';
        link.textContent = i;
        if (i === page) link.classList.add('active');
        link.addEventListener('click', (e) => {
            e.preventDefault();
            showPage(i);
        });
        pagination.appendChild(link);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadNews();
});