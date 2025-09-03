const API_BASE = window.location.protocol + '//' + window.location.host;

let adminTimezone = '';
let adminTimezoneOffset = '';

// Единый обработчик DOM
document.addEventListener('DOMContentLoaded', async () => {
    // Определяем часовой пояс админа
    detectAdminTimezone();
    
    const isLoggedIn = await checkAuth();
    if (!isLoggedIn) {
        showLogin();
    } else {
        hideLogin();
        loadSchedules();
        loadRecentLogs();
    }

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

// Определение часового пояса админа
function detectAdminTimezone() {
    try {
        adminTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const now = new Date();
        const offsetMinutes = -now.getTimezoneOffset();
        const offsetHours = offsetMinutes / 60;
        adminTimezoneOffset = offsetHours >= 0 ? `+${offsetHours}` : `${offsetHours}`;
        
        console.log(`Admin timezone: ${adminTimezone} (UTC${adminTimezoneOffset})`);
        updateTimezoneHints();
        
    } catch (error) {
        console.error('Ошибка определения часового пояса:', error);
        adminTimezone = 'UTC';
        adminTimezoneOffset = '+0';
    }
}

// Обновление подсказок о часовом поясе в форме
function updateTimezoneHints() {
    // Подсказка для cron
    const cronHint = document.getElementById('cronHint');
    if (cronHint) {
        cronHint.innerHTML = `ℹ️ Время указывается в часовом поясе ${adminTimezone} (UTC${adminTimezoneOffset})`;
    }
    
    // Подсказка для даты
    const dateHint = document.getElementById('dateHint');
    if (dateHint) {
        dateHint.innerHTML = `ℹ️ Время указывается в вашем часовом поясе ${adminTimezone} (UTC${adminTimezoneOffset})`;
    }
}


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
        container.innerHTML = '<div class="text-center text-muted py-4">Нет созданных рассылок</div>';
        return;
    }
    container.innerHTML = schedules.map(schedule => {
        const nextRunTime = schedule.next_run_time ? new Date(schedule.next_run_time).toLocaleString('ru-RU') : 'Не запланировано';
        const lastRunTime = schedule.last_run ? new Date(schedule.last_run).toLocaleString('ru-RU') : 'Никогда';
        const periodicity = schedule.schedule_config?.periodicity || '';
        let scheduleDisplay = '';
        if (periodicity === 'weekly') {
            scheduleDisplay = 'Еженедельно';
        } else if (periodicity === 'interval') {
            scheduleDisplay = `Интервал раз в ${schedule.schedule_config.days_interval} дней`;
        } else if (periodicity === 'single') {
            const datetime = schedule.schedule_config.datetime || 'не указано';
            const dtFormatted = datetime !== 'не указано' ? new Date(datetime).toLocaleString('ru-RU') : datetime;
            scheduleDisplay = 'Однократно: ' + dtFormatted;
        }
        return `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="card-title">${schedule.name}</h5>
                            ${schedule.description ? `<p class="card-text text-muted">${schedule.description}</p>` : ''}
                            <div class="row">
                                <div class="col-md-6">
                                    <small class="text-muted">
                                        <strong>Расписание:</strong> ${scheduleDisplay} (${schedule.admin_timezone || 'UTC'})
                                    </small>
                                </div>
                                <div class="col-md-6">
                                    <small class="text-muted">
                                        <strong>Следующий запуск:</strong> ${nextRunTime}
                                    </small><br>
                                    <small class="text-muted">
                                        <strong>Последний запуск:</strong> ${lastRunTime}
                                    </small>
                                </div>
                            </div>
                        </div>
                        <div class="btn-group-vertical">
                            <button class="btn btn-sm ${schedule.is_active ? 'btn-success' : 'btn-secondary'}" 
                                    onclick="toggleSchedule(${schedule.id}, ${!schedule.is_active})">
                                ${schedule.is_active ? 'Активна' : 'Неактивна'}
                            </button>
                            <button class="btn btn-sm btn-primary" onclick="runSchedule(${schedule.id})">
                                Запустить
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="editSchedule(${schedule.id})">
                                Изменить
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteSchedule(${schedule.id})">
                                Удалить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
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
    const periodicitySelect = document.getElementById('schedulePeriodicity');
    if (!periodicitySelect) {
        console.error('Element #schedulePeriodicity not found!');
        return;
    }
    const periodicity = periodicitySelect.value;
    document.getElementById('weeklyFields').classList.toggle('d-none', periodicity !== 'weekly');
    document.getElementById('intervalFields').classList.toggle('d-none', periodicity !== 'interval');
    document.getElementById('singleFields').classList.toggle('d-none', periodicity !== 'single');
}

// Вешаем обработчики на появление модального окна и изменение select
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('createModal');
    if (modal) {
        modal.addEventListener('shown.bs.modal', function() {
            toggleScheduleFields();  // вызываем при появлении формы
        });

        // Вешаем обработчик на изменение типа рассылки
        const periodicitySelect = document.getElementById('schedulePeriodicity');
        if (periodicitySelect) {
            periodicitySelect.addEventListener('change', toggleScheduleFields);
        }
    }
});

// Сохранение рассылки
async function saveSchedule() {
    const formData = new FormData(document.getElementById('scheduleForm'));
    const scheduleId = document.getElementById('scheduleId').value;
    const periodicity = document.getElementById('schedulePeriodicity').value;

    let scheduleConfig = {
        periodicity: periodicity,
        timezone: adminTimezone,
    };

    if (periodicity === 'weekly') {
        const days = [];
	    const weekdaysSelect = document.getElementById('weekdays');
	    for (let option of weekdaysSelect.selectedOptions) {
	        days.push(parseInt(option.value));
	    }
        scheduleConfig.days = days;
        scheduleConfig.hour = parseInt(document.getElementById('weeklyHour').value);
        scheduleConfig.minute = parseInt(document.getElementById('weeklyMinute').value);
    } else if (periodicity === 'interval') {
        scheduleConfig.days_interval = parseInt(document.getElementById('intervalDays').value);
        scheduleConfig.start_date = document.getElementById('intervalStartDate').value;
        scheduleConfig.hour = parseInt(document.getElementById('intervalHour').value);
        scheduleConfig.minute = parseInt(document.getElementById('intervalMinute').value);
    } else if (periodicity === 'single') {
        scheduleConfig.datetime = document.getElementById('singleDatetime').value;
    }

    const scheduleData = {
        name: formData.get('name'),
        description: formData.get('description'),
        schedule_config: scheduleConfig,
        is_active: formData.get('is_active') === 'on',
        admin_timezone: adminTimezone
    };

    // Обработка user_ids — без изменений
    const userIdsInput = formData.get('user_ids');
    if (userIdsInput && userIdsInput.trim()) {
        try {
            scheduleData.user_ids = userIdsInput.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        } catch (error) {
            showError('Неверный формат списка пользователей');
            return;
        }
    }

    // ... отправка на сервер — без изменений
    try {
        const url = scheduleId ? `${API_BASE}/schedules/${scheduleId}` : `${API_BASE}/schedules/`;
        const method = scheduleId ? 'PUT' : 'POST';
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scheduleData)
        });
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('createModal')).hide();
            loadSchedules();
            showSuccess(scheduleId ? 'Рассылка обновлена!' : 'Рассылка создана!');
        } else {
            const error = await response.json();
            showError(error.detail || 'Ошибка сохранения');
        }
    } catch (error) {
        showError('Ошибка: ' + error.message);
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

async function editSchedule(id) {
    try {
        const response = await fetch(`${API_BASE}/schedules/${id}`);
        const schedule = await response.json();
        const modal = new bootstrap.Modal('#createModal');
        modal.show();
        document.getElementById('createModal').addEventListener('shown.bs.modal', function () {
            // Базовые данные
            document.getElementById('modalTitle').textContent = 'Редактировать рассылку';
            document.getElementById('scheduleId').value = schedule.id;
            document.getElementById('scheduleName').value = schedule.name;
            document.getElementById('scheduleDescription').value = schedule.description || '';
            document.getElementById('schedulePeriodicity').value = schedule.schedule_config.periodicity || 'weekly';
            document.getElementById('userIds').value = schedule.user_ids ? schedule.user_ids.join(',') : '';
            document.getElementById('isActive').checked = schedule.is_active;

            // Заполняем дни недели и время для еженедельной рассылки
            const selectedDaysRaw = schedule.schedule_config.days || [];
            const selectedDays = selectedDaysRaw.map(d => parseInt(d));
            const weekdaysSelect = document.getElementById('weekdays');
            for (let option of weekdaysSelect.options) {
                const optionVal = parseInt(option.value);
                option.selected = selectedDays.includes(optionVal);
                console.log(`Day option: ${optionVal}, selected: ${option.selected}`);
            }
            document.getElementById('weeklyHour').value = schedule.schedule_config.hour || 12;
            document.getElementById('weeklyMinute').value = schedule.schedule_config.minute || 0;

            // Заполняем интервальную рассылку
            if (schedule.schedule_config.periodicity === 'interval') {
                document.getElementById('intervalStartDate').value = schedule.schedule_config.start_date || '';
                document.getElementById('intervalDays').value = schedule.schedule_config.days_interval || 1;
                document.getElementById('intervalHour').value = schedule.schedule_config.hour || 11;
                document.getElementById('intervalMinute').value = schedule.schedule_config.minute || 0;
            }

            // Заполняем однократную рассылку
            if (schedule.schedule_config.periodicity === 'single') {
                document.getElementById('singleDatetime').value = schedule.schedule_config.datetime || '';
            }

            // Переключаем видимость блоков
            toggleScheduleFields();
        }, { once: true });
    } catch (error) {
        alert('Ошибка загрузки данных рассылки');
    }
}

function showError(message) {
    // Можно использовать alert или создать красивое уведомление
    //alert('Ошибка: ' + message);
    
    // Или создать элемент для уведомлений:
     const errorDiv = document.getElementById('errorMessages');
     if (errorDiv) {
         errorDiv.innerHTML = `<div class="alert alert-danger">${message}</div>`;
         setTimeout(() => errorDiv.innerHTML = '', 5000);
     }
}

function showSuccess(message) {
    alert('Успех: ' + message);
    
    // Или аналогично для успешных сообщений:
     const successDiv = document.getElementById('successMessages');
     if (successDiv) {
         successDiv.innerHTML = `<div class="alert alert-success">${message}</div>`;
         setTimeout(() => successDiv.innerHTML = '', 3000);
     }
}

async function uploadCSV() {
    const fileInput = document.getElementById('csvFile');
    const spinner = document.getElementById('uploadSpinner');
    const resultsDiv = document.getElementById('csvResults');
    const resultsContent = document.getElementById('csvResultsContent');
    
    if (!fileInput.files[0]) {
        alert('Выберите CSV файл');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    spinner.classList.remove('d-none');
    
    try {
        const response = await fetch(`${API_BASE}/events/upload-csv/`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            resultsContent.innerHTML = `
                <div class="alert alert-success">
                    <strong>Обработано строк:</strong> ${result.results.total_rows}<br>
                    <strong>Успешно загружено:</strong> ${result.results.successful} событий<br>
                    <strong>Пропущено:</strong> ${result.results.failed} строк
                </div>
                ${result.results.errors.length > 0 ? `
                    <div class="alert alert-warning">
                        <strong>Ошибки (${result.results.errors.length}):</strong>
                        <ul class="mb-0 small">
                            ${result.results.errors.slice(0, 5).map(err => `<li>${err}</li>`).join('')}
                            ${result.results.errors.length > 5 ? '<li><em>... и другие</em></li>' : ''}
                        </ul>
                    </div>
                ` : ''}
            `;
        } else {
            resultsContent.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка загрузки: ${result.detail || 'Неизвестная ошибка'}
                </div>
            `;
        }
        
        resultsDiv.style.display = 'block';
        fileInput.value = '';
        
    } catch (error) {
        resultsContent.innerHTML = `
            <div class="alert alert-danger">
                Ошибка: ${error.message}
            </div>
        `;
        resultsDiv.style.display = 'block';
    } finally {
        spinner.classList.add('d-none');
    }
}

async function clearEvents() {
    const spinner = document.getElementById('clearSpinner');
    const clearResults = document.getElementById('csvResultsContent');
    const resultsDiv = document.getElementById('csvResults');
    
    if (!confirm('Вы точно хотите удалить ВСЕ события из базы?')) return;
    
    spinner.classList.remove('d-none');
    try {
        const response = await fetch(`${API_BASE}/events/clear-events/`, {
            method: 'POST',
            credentials: 'include'
        });
        const result = await response.json();
        
        if (response.ok) {
            clearResults.innerHTML = `
                <div class="alert alert-success">
                    <strong>Удалено:</strong> ${result.message}
                </div>
            `;
            resultsDiv.style.display = 'block';
        } else {
            clearResults.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка: ${result.detail || 'Неизвестная ошибка'}
                </div>
            `;
            resultsDiv.style.display = 'block';
        }
    } catch (error) {
        clearResults.innerHTML = `
            <div class="alert alert-danger">
                Ошибка: ${error.message}
            </div>
        `;
        resultsDiv.style.display = 'block';
    } finally {
        spinner.classList.add('d-none');
    }
}

