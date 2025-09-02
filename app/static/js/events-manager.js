const API_BASE = window.location.protocol + '//' + window.location.host;
let currentPage = 0;
let eventsPerPage = 100;
let currentEvents = [];
let totalEventsCount = 0;

// Загрузка при старте страницы
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // Устанавливаем значение по умолчанию
    document.getElementById('eventsPerPageSelect').value = eventsPerPage;
    
    loadEvents();
});

async function checkAuth() {
    try {
        const response = await fetch('/admin/newsletter/logs/', {
            method: 'GET',
            credentials: 'include'
        });
        if (!response.ok) {
            window.location.href = '/admin';
        }
    } catch (err) {
        window.location.href = '/admin';
    }
}

// Получение общего количества событий
async function fetchEventsCount() {
    try {
        const response = await fetch(`${API_BASE}/events/count`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            totalEventsCount = data.count;
        }
    } catch (error) {
        console.error('Ошибка получения количества событий:', error);
    }
}

// Загрузка событий
async function loadEvents() {
    document.getElementById('eventsLoading').style.display = 'block';
    document.getElementById('eventsTable').style.display = 'none';
    
    try {
        // Сначала получаем общее количество
        await fetchEventsCount();
        
        let url = `${API_BASE}/events/?skip=${currentPage * eventsPerPage}&limit=${eventsPerPage}`;
        
        const response = await fetch(url, { credentials: 'include' });
        const events = await response.json();
        
        currentEvents = events;
        renderEvents(events);
        renderPagination();
        
    } catch (error) {
        console.error('Ошибка загрузки событий:', error);
        alert('Ошибка загрузки событий');
    } finally {
        document.getElementById('eventsLoading').style.display = 'none';
        document.getElementById('eventsTable').style.display = 'block';
    }
}

// Отображение событий в таблице
function renderEvents(events) {
    const tbody = document.getElementById('eventsTableBody');
    const totalPages = Math.ceil(totalEventsCount / eventsPerPage);
    
    // Обновляем информацию
    document.getElementById('eventsInfo').textContent = 
        `Страница ${currentPage + 1} из ${totalPages} (всего событий: ${totalEventsCount})`;
    
    if (events.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-4">
                    <i class="bi bi-calendar-x fs-1"></i>
                    <p class="mt-2">События не найдены</p>
                </td>
            </tr>
        `;
        return;
    }
    
    // Сортируем события по дате перед отображением
    const sortedEvents = sortEventsByDate([...events]);
    
    tbody.innerHTML = sortedEvents.map(event => `
        <tr>
            <td>${event.id}</td>
            <td>
                <div class="fw-bold">${event.title}</div>
                ${event.mark ? `<small class="text-muted">${event.mark}</small>` : ''}
            </td>
            <td>${event.category || '-'}</td>
            <td>${event.city || '-'}</td>
            <td>
                ${event.dates && event.dates.length > 0 ? 
                    event.dates.slice(0, 2).join(', ') + (event.dates.length > 2 ? '...' : '') 
                    : '-'}
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="editEvent(${event.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteEvent(${event.id}, '${event.title}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Улучшенная пагинация с точным количеством страниц
function renderPagination() {
    const pagination = document.getElementById('pagination');
    
    const totalPages = Math.ceil(totalEventsCount / eventsPerPage);
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Кнопка "Предыдущая"
    paginationHTML += `
        <li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Логика отображения номеров страниц
    const startPage = Math.max(0, currentPage - 2);
    const endPage = Math.min(totalPages - 1, currentPage + 2);
    
    // Первая страница + многоточие (если нужно)
    if (startPage > 0) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(0)">1</a>
            </li>
        `;
        if (startPage > 1) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Основные страницы
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i + 1}</a>
            </li>
        `;
    }
    
    // Многоточие + последняя страница (если нужно)
    if (endPage < totalPages - 1) {
        if (endPage < totalPages - 2) {
            paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="changePage(${totalPages - 1})">${totalPages}</a>
            </li>
        `;
    }
    
    // Поле ручного ввода с ограничением
    paginationHTML += `
        <li class="page-item">
            <span class="page-link p-1">
                <input type="number" 
                       id="pageInput" 
                       class="form-control form-control-sm d-inline-block" 
                       style="width: 70px;" 
                       min="1" 
                       max="${totalPages}"
                       value="${currentPage + 1}"
                       onkeypress="handlePageInputEnter(event)"
                       placeholder="/${totalPages}">
            </span>
        </li>
        <li class="page-item">
            <a class="page-link" href="#" onclick="goToInputPage()">
                <i class="bi bi-arrow-right"></i>
            </a>
        </li>
    `;
    
    // Кнопка "Следующая"
    paginationHTML += `
        <li class="page-item ${currentPage >= totalPages - 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = paginationHTML;
}

function changePage(newPage) {
    const totalPages = Math.ceil(totalEventsCount / eventsPerPage);
    if (newPage >= 0 && newPage < totalPages) {
        currentPage = newPage;
        loadEvents();
    }
}

// Изменение количества событий на странице
function changeEventsPerPage() {
    const select = document.getElementById('eventsPerPageSelect');
    eventsPerPage = parseInt(select.value);
    currentPage = 0; // Сбрасываем на первую страницу
    loadEvents();
}

// Открытие модального окна создания
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Новое событие';
    document.getElementById('eventForm').reset();
    document.getElementById('eventId').value = '';
    new bootstrap.Modal(document.getElementById('eventModal')).show();
}

// Редактирование события
async function editEvent(eventId) {
    try {
        const response = await fetch(`${API_BASE}/events/${eventId}`, {
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error('Событие не найдено');
        
        const event = await response.json();
        
        // Заполняем форму
        document.getElementById('modalTitle').textContent = 'Редактировать событие';
        document.getElementById('eventId').value = event.id;
        document.getElementById('eventTitle').value = event.title || '';
        document.getElementById('eventUrl').value = event.url || '';
        document.getElementById('eventCategory').value = event.category || '';
        document.getElementById('eventMark').value = event.mark || '';
        document.getElementById('eventCity').value = event.city || '';
        document.getElementById('eventAgeRestriction').value = event.age_restriction || '';
        document.getElementById('eventDescription').value = event.description || '';
        document.getElementById('eventText').value = event.text || '';
        document.getElementById('eventPhoto').value = event.photo || '';
        document.getElementById('eventDates').value = event.dates ? event.dates.join(', ') : '';
        document.getElementById('eventLanguages').value = event.languages ? event.languages.join(', ') : '';
        
        new bootstrap.Modal(document.getElementById('eventModal')).show();
        
    } catch (error) {
        alert('Ошибка загрузки события: ' + error.message);
    }
}

// Сохранение события
async function saveEvent() {
    const form = document.getElementById('eventForm');
    const saveSpinner = document.getElementById('saveSpinner');
    const saveButtonText = document.getElementById('saveButtonText');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    saveSpinner.classList.remove('d-none');
    saveButtonText.textContent = 'Сохранение...';
    
    try {
        const eventId = document.getElementById('eventId').value;
        const isEdit = eventId !== '';
        
        // Собираем данные формы
        const formData = {
            title: document.getElementById('eventTitle').value,
            url: document.getElementById('eventUrl').value,
            category: document.getElementById('eventCategory').value || null,
            mark: document.getElementById('eventMark').value || null,
            city: document.getElementById('eventCity').value || null,
            age_restriction: document.getElementById('eventAgeRestriction').value || null,
            description: document.getElementById('eventDescription').value || null,
            text: document.getElementById('eventText').value || null,
            photo: document.getElementById('eventPhoto').value || null,
            dates: document.getElementById('eventDates').value ? 
                   document.getElementById('eventDates').value.split(',').map(d => d.trim()) : [],
            languages: document.getElementById('eventLanguages').value ? 
                      document.getElementById('eventLanguages').value.split(',').map(l => l.trim()) : []
        };
        
        const url = isEdit ? `${API_BASE}/events/${eventId}` : `${API_BASE}/events/`;
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка сохранения');
        }
        
        bootstrap.Modal.getInstance(document.getElementById('eventModal')).hide();
        loadEvents(); // Перезагружаем список
        alert(isEdit ? 'Событие обновлено!' : 'Событие создано!');
        
    } catch (error) {
        alert('Ошибка: ' + error.message);
    } finally {
        saveSpinner.classList.add('d-none');
        saveButtonText.textContent = 'Сохранить';
    }
}

// Удаление события
async function deleteEvent(eventId, eventTitle) {
    if (!confirm(`Вы уверены, что хотите удалить событие "${eventTitle}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/events/${eventId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка удаления события');
        }
        
        loadEvents(); // Перезагружаем список
        alert('Событие удалено!');
        
    } catch (error) {
        alert('Ошибка удаления: ' + error.message);
    }
}

// Переход на введенную страницу с проверкой
function goToInputPage() {
    const pageInput = document.getElementById('pageInput');
    const pageNumber = parseInt(pageInput.value);
    const totalPages = Math.ceil(totalEventsCount / eventsPerPage);
    
    if (pageNumber && pageNumber > 0 && pageNumber <= totalPages) {
        changePage(pageNumber - 1); // Конвертируем в 0-based индекс
    } else {
        alert(`Введите номер страницы от 1 до ${totalPages}`);
        pageInput.value = currentPage + 1; // Возвращаем старое значение
    }
}

// Обработка Enter в поле ввода
function handlePageInputEnter(event) {
    if (event.key === 'Enter') {
        goToInputPage();
    }
}

// Улучшенная функция для парсинга русских дат
function parseRussianDate(dateStr) {
    if (!dateStr || dateStr.trim() === '-' || dateStr.trim() === '') {
        return new Date(0); // Возвращаем минимальную дату для пустых значений
    }
    
    const months = {
        'января': 0, 'февраля': 1, 'марта': 2, 'апреля': 3,
        'мая': 4, 'июня': 5, 'июля': 6, 'августа': 7,
        'сентября': 8, 'октября': 9, 'ноября': 10, 'декабря': 11
    };
    
    const str = dateStr.trim().toLowerCase();
    
    // Ищем первое число в строке (для случаев "28-31 августа" берем "28")
    const numberMatch = str.match(/^\d+/);
    if (!numberMatch) {
        return new Date(0);
    }
    
    const day = parseInt(numberMatch[0]);
    
    // Ищем название месяца
    let monthIndex = -1;
    for (const [monthName, index] of Object.entries(months)) {
        if (str.includes(monthName)) {
            monthIndex = index;
            break;
        }
    }
    
    if (monthIndex === -1) {
        return new Date(0);
    }
    
    // Используем текущий год для сортировки
    const currentYear = new Date().getFullYear();
    return new Date(currentYear, monthIndex, day);
}

// Функция сортировки событий по первой дате
function sortEventsByDate(events) {
    return events.sort((a, b) => {
        const dateA = a.dates && a.dates.length > 0 ? parseRussianDate(a.dates[0]) : new Date(0);
        const dateB = b.dates && b.dates.length > 0 ? parseRussianDate(b.dates[0]) : new Date(0);
        
        // События с пустыми датами в конец списка
        if (dateA.getTime() === 0 && dateB.getTime() === 0) return 0;
        if (dateA.getTime() === 0) return 1;
        if (dateB.getTime() === 0) return -1;
        
        return dateA - dateB; // По возрастанию (ближайшие даты сначала)
    });
}

