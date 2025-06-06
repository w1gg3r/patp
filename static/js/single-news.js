// Получаем id из URL вида /single-news/1
const pathSegments = window.location.pathname.split('/');
const newsId = parseInt(pathSegments[pathSegments.length - 1], 10);

console.log("ID новости:", newsId); // Для проверки

function renderNews(news) {
    const container = document.getElementById('news-detail');
    const titleElement = document.getElementById('news-title');

    if (!news || !news.title) {
        container.innerHTML = `<p>Новость не найдена.</p>`;
        return;
    }

    // Обновляем заголовок в хлебных крошках
    titleElement.textContent = news.title;

    // Рендерим новость
    container.innerHTML = `
        <h2>${news.title}</h2>
        <div class="news-container">
            <div class="news-image">
                <img src="${news.image}" alt="${news.title}">
                <span class="date-overlay">${news.date}</span>
            </div>
            <div class="news-description">
                <p>${news.description}</p>
            </div>
        </div>
        <a href="/news" class="back-link">&larr; Вернуться к новостям</a>
    `;
}

window.onload = () => {
    if (!newsId || isNaN(newsId)) {
        document.getElementById('news-detail').innerHTML = `<p>Не указан или неверный ID новости.</p>`;
        return;
    }

    // Загружаем новость с сервера
    fetch(`/api/news/${newsId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Ошибка сети");
            }
            return response.json();
        })
        .then(news => {
            // Корректируем формат даты, если нужно (заменяем / на .)
            news.date = news.date.replace(/\//g, '.');

            renderNews(news);
        })
        .catch(error => {
            console.error('Ошибка загрузки новости:', error);
            document.getElementById('news-detail').innerHTML = `<p>Новость не найдена или произошла ошибка.</p>`;
        });
};