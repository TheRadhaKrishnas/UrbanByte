// auth.js – Uses Flask backend and stores all user fields

async function login(event) {
  event.preventDefault();
  const role = document.querySelector('.role-btn.active')?.getAttribute('data-role') || 'member';
  const loginCode = document.getElementById('loginCode').value.trim();
  const loginPassword = document.getElementById('loginPassword').value.trim();

  if (!loginCode || !loginPassword) {
    alert('Please enter both code and password');
    return;
  }

  try {
    const response = await fetch('http://localhost:5000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ member_code: loginCode, password: loginPassword })
    });
    const data = await response.json();
    if (response.ok) {
      // Store full user data (includes age, gender, family_members)
      sessionStorage.setItem('user', JSON.stringify(data.user));
      // Redirect based on role
      if (data.user.role === 'member') {
        window.location.href = 'member-dashboard.html';
      } else {
        window.location.href = 'management-dashboard.html';
      }
    } else {
      alert(data.error || 'Login failed');
    }
  } catch (err) {
    console.error('Login error:', err);
    alert('Could not connect to backend. Is it running?');
  }
}

async function register(event) {
  event.preventDefault();
  const name = document.getElementById('regName').value.trim();
  const apartment = document.getElementById('regApartment').value.trim();
  const flat = document.getElementById('regFlat').value.trim();
  const memberCode = document.getElementById('regCode').value.trim();
  const phone = document.getElementById('regPhone').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value.trim();

  if (!name || !apartment || !flat || !memberCode || !phone || !email || !password) {
    alert('Please fill all fields');
    return;
  }

  try {
    const response = await fetch('http://localhost:5000/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name, flat, member_code: memberCode, phone, email, password
      })
    });
    const data = await response.json();
    if (response.ok) {
      alert('Registration successful! Please login.');
    } else {
      alert(data.error || 'Registration failed');
    }
  } catch (err) {
    console.error('Register error:', err);
    alert('Could not connect to backend.');
  }
}

function logout() {
  sessionStorage.removeItem('user');
  window.location.href = 'index.html';
}

function checkAuth(allowedRoles = ['member', 'management']) {
  const userJson = sessionStorage.getItem('user');
  if (!userJson) {
    window.location.href = 'index.html';
    return null;
  }
  const user = JSON.parse(userJson);
  if (!allowedRoles.includes(user.role)) {
    if (user.role === 'member') {
      window.location.href = 'member-dashboard.html';
    } else {
      window.location.href = 'management-dashboard.html';
    }
    return null;
  }
  return user;
}

// Role selector and form attachments
document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) loginForm.addEventListener('submit', login);
  const registerForm = document.getElementById('registerForm');
  if (registerForm) registerForm.addEventListener('submit', register);
  const roleBtns = document.querySelectorAll('.role-btn');
  roleBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      roleBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
    });
  });
});