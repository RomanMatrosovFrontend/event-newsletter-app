const API_BASE = 'http://' + window.location.hostname + ':8000';

// Единый обработчик DOM
document.addEventListener('DOMContentLoaded', async () => {
    const isLoggedIn = await checkAuth();
    if (!isLoggedIn) {
        showLogin();
    } else {
        hideLogin();
        loadSchedules();
        loadRecentLogs();
    }

    // Сброс формы при открытии модального окна
    const modal = document.getElementById('createModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function () {
            document.getElementById('modalTitle').textContent = 'Создать рассылку';
            document.getElementById('scheduleForm').reset();
            document.getElementById('scheduleId').value = '';
            toggleScheduleFields();
        });
    }
});

async function checkAuth() {
    try {
        const response = await fetch('/admin/newsletter/logs/', {
            method: 'GET',
            credentials: 'include'
        });
        return response.ok;
    } catch (err) {
        return false;
    }
}


function showLogin() {
    document.getElementById('mainApp').classList.add('d-none');
    document.getElementById('loginForm').classList.remove('d-none');
}

function hideLogin() {
    document.getElementById('loginForm').classList.add('d-none');
    document.getElementById('mainApp').classList.remove('d-none');
}

function getCookie(name) {
    let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
}

document.getElementById('login')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');

    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password }),
            credentials: 'include'
        });

        if (response.ok) {
            hideLogin();
            loadSchedules();
            loadRecentLogs();
        } else {
            errorDiv.classList.remove('d-none');
        }
    } catch (err) {
        errorDiv.textContent = 'Ошибка подключения';
        errorDiv.classList.remove('d-none');
    }
});

function logout() {
    fetch('/admin/logout', {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        location.reload();
    });
}

// Загрузка всех рассылок
async function loadSchedules() {
    try {
        const response = await fetch(`${API_BASE}/schedules/`);
        const schedules = await response.json();
        renderSchedules(schedules);
    } catch (error) {
        console.error('Ошибка загрузки рассылок:', error);
        document.getElementById('schedulesList').innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            </div>
        `;
    }
}

// Отображение рассылок
function renderSchedules(schedules) {
    const container = document.getElementById('schedulesList');
    
    if (schedules.length === 0) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> Нет созданных рассылок
                </div>
            </div>
        `;
        return;
    }

    container.innerHTML = schedules.map(schedule => `
        <div class="col-md-6 mb-3">
            <div class="card schedule-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">${schedule.name}</h6>
                    <span class="badge ${schedule.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${schedule.is_active ? 'Активно' : 'Неактивно'}
                    </span>
                </div>
                <div class="card-body">
                    ${schedule.description ? `<p class="card-text">${schedule.description}</p>` : ''}
                    
                    <div class="mb-2">
                        <strong>Тип:</strong> 
                        ${schedule.schedule_type === 'cron' ? 'Периодическая' : 'Однократная'}
                    </div>
                    
                    ${schedule.schedule_type === 'cron' ? `
                        <div class="mb-2">
                            <strong>Cron:</strong> 
                            <span class="badge bg-primary cron-badge">${schedule.cron_expression}</span>
                        </div>
                    ` : `
                        <div class="mb-2">
                            <strong>Дата:</strong> 
                            ${new Date(schedule.specific_date).toLocaleString('ru-RU')}
                        </div>
                    `}
                    
                    ${schedule.user_ids && schedule.user_ids.length > 0 ? `
                        <div class="mb-2">
                            <strong>Пользователи:</strong> 
                            <span class="badge bg-info">${schedule.user_ids.join(', ')}</span>
                        </div>
                    ` : ''}
                    
                    ${schedule.last_run ? `
                        <div class="mb-2">
                            <strong>Последний запуск:</strong> 
                            ${new Date(schedule.last_run).toLocaleString('ru-RU')}
                        </div>
                    ` : ''}
                    
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editSchedule(${schedule.id})">
                            <i class="bi bi-pencil"></i> Изменить
                        </button>
                        <button class="btn btn-outline-success" onclick="runSchedule(${schedule.id})">
                            <i class="bi bi-play"></i> Запустить
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteSchedule(${schedule.id})">
                            <i class="bi bi-trash"></i> Удалить
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Загрузка последних логов
async function loadRecentLogs() {
    try {
        const response = await fetch(`${API_BASE}/admin/newsletter/logs/`, {
            method: 'GET',
            credentials: 'include'
        });
        const logs = await response.json();
        renderRecentLogs(logs);
    } catch (error) {
        console.error('Ошибка загрузки логов:', error);
    }
}

function renderRecentLogs(logs) {
    const container = document.getElementById('recentLogs');
    
    if (!logs || logs.length === 0) {
        container.innerHTML = '<small class="text-muted">Нет данных о запусках</small>';
        return;
    }

    container.innerHTML = logs.slice(0, 5).map(log => `
        <div class="mb-2">
            <small>${new Date(log.sent_at).toLocaleString('ru-RU')}</small><br>
            <span class="badge bg-success">✓ ${log.successful_sends}</span>
            <span class="badge bg-danger">✗ ${log.failed_sends}</span>
            <span class="badge bg-secondary">${log.duration_seconds}s</span>
        </div>
    `).join('');
}

// Переключение полей в форме
function toggleScheduleFields() {
    const type = document.getElementById('scheduleType').value;
    document.getElementById('cronField').classList.toggle('d-none', type !== 'cron');
    document.getElementById('dateField').classList.toggle('d-none', type !== 'date');
}

// Редактирование рассылки
async function editSchedule(id) {
    try {
        const response = await fetch(`${API_BASE}/schedules/${id}`);
        const schedule = await response.json();

        // Открываем модалку
        const modal = new bootstrap.Modal('#createModal');
        modal.show();

        // Ждём, когда модалка полностью появится
        document.getElementById('createModal').addEventListener('shown.bs.modal', function () {
            // Теперь безопасно заполняем
            document.getElementById('modalTitle').textContent = 'Редактировать рассылку';
            document.getElementById('scheduleId').value = schedule.id;
            document.getElementById('scheduleName').value = schedule.name;
            document.getElementById('scheduleDescription').value = schedule.description || '';
            document.getElementById('scheduleType').value = schedule.schedule_type;
            document.getElementById('cronExpression').value = schedule.cron_expression || '';
            document.getElementById('specificDate').value = schedule.specific_date ? schedule.specific_date.slice(0, 16) : '';
            document.getElementById('userIds').value = schedule.user_ids ? schedule.user_ids.join(',') : '';
            document.getElementById('isActive').checked = schedule.is_active;

            // Обновляем видимость полей
            toggleScheduleFields();
        }, { once: true });

    } catch (error) {
        alert('Ошибка загрузки данных рассылки');
    }
}

// Сохранение рассылки
async function saveSchedule() {
    const formData = {
        name: document.getElementById('scheduleName').value,
        description: document.getElementById('scheduleDescription').value,
        schedule_type: document.getElementById('scheduleType').value,
        cron_expression: document.getElementById('cronExpression').value || null,
        specific_date: document.getElementById('specificDate').value || null,
        user_ids: document.getElementById('userIds').value 
            ? document.getElementById('userIds').value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
            : null,
        is_active: document.getElementById('isActive').checked
    };

    const id = document.getElementById('scheduleId').value;
    const url = id ? `${API_BASE}/schedules/${id}` : `${API_BASE}/schedules/`;
    const method = id ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('createModal')).hide();
            loadSchedules();
            alert(id ? 'Рассылка обновлена!' : 'Рассылка создана!');
        } else {
            alert('Ошибка сохранения: ' + response.statusText);
        }
    } catch (error) {
        alert('Ошибка сети: ' + error.message);
    }
}

// Запуск рассылки
async function runSchedule(id) {
    if (!confirm('Запустить рассылку сейчас?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/schedules/${id}/run`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            alert('Рассылка запущена!');
            loadRecentLogs();
        } else {
            alert('Ошибка запуска рассылки');
        }
    } catch (error) {
        alert('Ошибка сети: ' + error.message);
    }
}

// Удаление рассылки
async function deleteSchedule(id) {
    if (!confirm('Удалить эту рассылку?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/schedules/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            alert('Рассылка удалена!');
            loadSchedules();
        } else {
            alert('Ошибка удаления рассылки');
        }
    } catch (error) {
        alert('Ошибка сети: ' + error.message);
    }
}

// Смена логина/пароля
async function changeCredentials() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newUsername = document.getElementById('newUsername').value;
    const newPassword = document.getElementById('newPassword').value;

    if (!currentPassword) {
        alert('Введите текущий пароль');
        return;
    }

    const data = { current_password: currentPassword };
    if (newUsername) data.new_username = newUsername;
    if (newPassword) data.new_password = newPassword;

    try {
        const response = await fetch('/admin/change-credentials', {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        if (response.ok) {
            alert('Данные успешно изменены');
            bootstrap.Modal.getInstance(document.getElementById('changeCredentialsModal')).hide();
            document.getElementById('changeCredentialsForm').reset();
        } else {
            alert(result.detail || 'Ошибка при изменении данных');
        }
    } catch (error) {
        alert('Ошибка соединения');
    }
}

// Создание админа
async function createAdmin() {
    const username = document.getElementById('adminUsername').value;
    const password = document.getElementById('adminPassword').value;

    if (!username || !password) {
        alert('Заполните все поля');
        return;
    }

    try {
        const response = await fetch('/admin/create-admin', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();
        
        if (response.ok) {
            alert('Админ успешно создан');
            bootstrap.Modal.getInstance(document.getElementById('createAdminModal')).hide();
            document.getElementById('createAdminForm').reset();
        } else {
            alert(result.detail || 'Ошибка при создании админа');
        }
    } catch (error) {
        alert('Ошибка соединения');
    }
}

