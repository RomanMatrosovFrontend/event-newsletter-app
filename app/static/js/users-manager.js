const API_BASE = window.location.protocol + '//' + window.location.host;
let currentPage = 0;
let usersPerPage = 100;
let totalUsersCount = 0;

// Загрузка страницы
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
  document.getElementById('usersPerPageSelect').value = usersPerPage;
  loadUsers();
});

async function checkAuth() {
  try {
    const resp = await fetch('/admin/newsletter/logs/', { credentials: 'include' });
    if (!resp.ok) window.location.href = '/admin';
  } catch {
    window.location.href = '/admin';
  }
}

async function fetchUsersCount() {
  try {
    const resp = await fetch(`${API_BASE}/users/?skip=0&limit=1`, { credentials: 'include' });
    if (resp.ok) {
      const total = resp.headers.get('X-Total-Count');
      totalUsersCount = total ? parseInt(total, 10) : 0;
    }
  } catch (error) {
    console.error('Ошибка получения количества пользователей:', error);
  }
}

async function loadUsers() {
  document.getElementById('usersLoading').style.display = 'block';
  document.getElementById('usersTable').style.display = 'none';

  await fetchUsersCount();

  const url = `${API_BASE}/users/?skip=${currentPage * usersPerPage}&limit=${usersPerPage}`;
  try {
    const resp = await fetch(url, { credentials: 'include' });
    const users = await resp.json();
    renderUsers(users);
    renderPagination();
  } catch (error) {
    console.error('Ошибка загрузки пользователей:', error);
    alert('Ошибка загрузки пользователей');
  } finally {
    document.getElementById('usersLoading').style.display = 'none';
    document.getElementById('usersTable').style.display = 'block';
  }
}

function renderUsers(users) {
  const tbody = document.getElementById('usersTableBody');
  const totalPages = Math.ceil(totalUsersCount / usersPerPage);
  document.getElementById('usersInfo').textContent =
    `Страница ${currentPage + 1} из ${totalPages} (всего: ${totalUsersCount})`;

  if (!users.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted py-4">
          <i class="bi bi-emoji-frown fs-1"></i>
          <p class="mt-2">Нет пользователей</p>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = users.map(u => `
    <tr>
      <td>${u.id}</td>
      <td>${u.email}</td>
      <td>${u.is_subscribed ? 'Да' : 'Нет'}</td>
      <td>${new Date(u.created_at).toLocaleString()}</td>
      <td>${new Date(u.updated_at).toLocaleString()}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary me-1" onclick="editUser(${u.id})">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${u.id}, '${u.email}')">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    </tr>
  `).join('');
}

function renderPagination() {
  const pagination = document.getElementById('paginationUsers');
  const totalPages = Math.ceil(totalUsersCount / usersPerPage);
  if (totalPages <= 1) {
    pagination.innerHTML = '';
    return;
  }

  let html = '';
  html += `
    <li class="page-item ${currentPage === 0 ? 'disabled' : ''}">
      <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
        <i class="bi bi-chevron-left"></i>
      </a>
    </li>
  `;

  const start = Math.max(0, currentPage - 2);
  const end = Math.min(totalPages - 1, currentPage + 2);

  if (start > 0) {
    html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(0)">1</a></li>`;
    if (start > 1) html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
  }

  for (let i = start; i <= end; i++) {
    html += `
      <li class="page-item ${i === currentPage ? 'active' : ''}">
        <a class="page-link" href="#" onclick="changePage(${i})">${i + 1}</a>
      </li>
    `;
  }

  if (end < totalPages - 1) {
    if (end < totalPages - 2) html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    html += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages - 1})">${totalPages}</a></li>`;
  }

  html += `
    <li class="page-item">
      <span class="page-link p-1">
        <input type="number" id="pageInput" class="form-control form-control-sm d-inline-block"
               style="width:70px" min="1" max="${totalPages}" value="${currentPage + 1}"
               onkeypress="handlePageInputEnter(event)" placeholder="/${totalPages}">
      </span>
    </li>
    <li class="page-item">
      <a class="page-link" href="#" onclick="goToInputPage()">
        <i class="bi bi-arrow-right"></i>
      </a>
    </li>
  `;

  html += `
    <li class="page-item ${currentPage >= totalPages - 1 ? 'disabled' : ''}">
      <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
        <i class="bi bi-chevron-right"></i>
      </a>
    </li>
  `;

  pagination.innerHTML = html;
}

function changePage(newPage) {
  const totalPages = Math.ceil(totalUsersCount / usersPerPage);
  if (newPage >= 0 && newPage < totalPages) {
    currentPage = newPage;
    loadUsers();
  }
}

function changeUsersPerPage() {
  usersPerPage = parseInt(document.getElementById('usersPerPageSelect').value, 10);
  currentPage = 0;
  loadUsers();
}

function openCreateModal() {
  document.getElementById('modalTitle').textContent = 'Новый пользователь';
  document.getElementById('userForm').reset();
  document.getElementById('userId').value = '';
  loadFormMetadata();
  new bootstrap.Modal(document.getElementById('userModal')).show();
}

async function loadFormMetadata() {
  const categories = [
    'Афиша (концерты)', 'Афиша (театры)', 'Афиша (выставки)', 'Афиша (спорт)'
    // допишите все остальные категории
  ];
  const cities = ['Будва','Подгорица','Херцег-Нови','Тиват','Бар','Другие города'];
  const types = ['weekly','monthly','bi_monthly'];

  const cats = document.getElementById('categoriesBlock');
  cats.innerHTML = categories.map(c => `
    <div class="form-check me-3">
      <input class="form-check-input" type="checkbox" value="${c}">
      <label class="form-check-label">${c}</label>
    </div>
  `).join('');

  const cityBlock = document.getElementById('citiesBlock');
  cityBlock.innerHTML = cities.map(c => `
    <div class="form-check me-3">
      <input class="form-check-input" type="checkbox" value="${c}">
      <label class="form-check-label">${c}</label>
    </div>
  `).join('');

  const typesBlock = document.getElementById('typesBlock');
  typesBlock.innerHTML = types.map(t => `
    <div class="form-check me-3">
      <input class="form-check-input" type="checkbox" value="${t}">
      <label class="form-check-label">${t}</label>
    </div>
  `).join('');
}

async function editUser(id) {
  try {
    const resp = await fetch(`${API_BASE}/users/${id}`, { credentials: 'include' });
    if (!resp.ok) throw new Error('Пользователь не найден');
    const u = await resp.json();

    document.getElementById('modalTitle').textContent = 'Редактировать пользователя';
    document.getElementById('userId').value = u.id;
    document.getElementById('userEmail').value = u.email;
    document.getElementById('userSubscribed').checked = u.is_subscribed;

    loadFormMetadata();
    setTimeout(() => {
      // Установить значения чекбоксов
      u.categories.forEach(c => {
        const inp = Array.from(document.querySelectorAll('#categoriesBlock input')).find(i => i.value === c);
        if (inp) inp.checked = true;
      });
      u.cities.forEach(c => {
        const inp = Array.from(document.querySelectorAll('#citiesBlock input')).find(i => i.value === c);
        if (inp) inp.checked = true;
      });
      u.subscription_types.forEach(t => {
        const inp = Array.from(document.querySelectorAll('#typesBlock input')).find(i => i.value === t);
        if (inp) inp.checked = true;
      });
    }, 100);

    new bootstrap.Modal(document.getElementById('userModal')).show();
  } catch (error) {
    alert('Ошибка загрузки пользователя: ' + error.message);
  }
}

async function saveUser() {
  const form = document.getElementById('userForm');
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const id = document.getElementById('userId').value;
  const payload = {
    email: document.getElementById('userEmail').value,
    is_subscribed: document.getElementById('userSubscribed').checked,
    categories: Array.from(document.querySelectorAll('#categoriesBlock input:checked')).map(i => i.value),
    cities: Array.from(document.querySelectorAll('#citiesBlock input:checked')).map(i => i.value),
    subscription_types: Array.from(document.querySelectorAll('#typesBlock input:checked')).map(i => i.value)
  };

  const url = id ? `${API_BASE}/users/${id}` : `${API_BASE}/users/`;
  const method = id ? 'PUT' : 'POST';

  try {
    const resp = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
    if (!resp.ok) {
      const { detail } = await resp.json();
      throw new Error(detail || 'Ошибка сохранения');
    }
    bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
    loadUsers();
    alert(id ? 'Пользователь обновлён!' : 'Пользователь создан!');
  } catch (error) {
    alert('Ошибка: ' + error.message);
  }
}

async function deleteUser(id, email) {
  if (!confirm(`Удалить пользователя ${email}?`)) return;
  try {
    const resp = await fetch(`${API_BASE}/users/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    if (!resp.ok) throw new Error('Ошибка удаления');
    loadUsers();
    alert('Пользователь удалён!');
  } catch (error) {
    alert('Ошибка удаления: ' + error.message);
  }
}

function goToInputPage() {
  const inp = document.getElementById('pageInput');
  const page = parseInt(inp.value, 10);
  const totalPages = Math.ceil(totalUsersCount / usersPerPage);
  if (page >= 1 && page <= totalPages) {
    changePage(page - 1);
  } else {
    alert(`Введите номер страницы от 1 до ${totalPages}`);
    inp.value = currentPage + 1;
  }
}

function handlePageInputEnter(event) {
  if (event.key === 'Enter') goToInputPage();
}

