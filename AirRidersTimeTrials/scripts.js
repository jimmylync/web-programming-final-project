// =================== CONFIG ===================
const API_BASE = "http://127.0.0.1:5000";

// =================== AUTH HELPERS ===================
function getToken() {
  return localStorage.getItem("access_token");
}
function isLoggedIn() {
  return !!getToken();
}
function authHeaders(extra = {}) {
  return {
    ...extra,
    Authorization: `Bearer ${getToken()}`
  };
}
function logoutNow() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  updateTopNav();
}

// =================== MODALS ===================
function openModal(id) {
  document.getElementById(id).classList.add("active");
}
function closeModals() {
  document.querySelectorAll(".modal").forEach(m => m.classList.remove("active"));
}
document.querySelectorAll(".modal-close").forEach(btn => {
  btn.addEventListener("click", closeModals);
});

// =================== NAV (top bar) ===================
function updateTopNav() {
  const nav = document.querySelector(".top-links");
  if (!nav) return;

  if (isLoggedIn()) {
    nav.innerHTML = `
      <a href="#" id="upload-btn">Upload</a> |
      <a href="#" id="profile-btn">Edit Profile</a> |
      <a href="#" id="logout-btn">Log out</a>
    `;
  } else {
    nav.innerHTML = `
      <a href="#" id="upload-btn">Upload</a> |
      <a href="#" id="login-btn">Log in</a> |
      <a href="#" id="register-btn">Register</a>
    `;
  }

  attachNavHandlers();
}

function attachNavHandlers() {
  const upload = document.getElementById("upload-btn");
  const login = document.getElementById("login-btn");
  const register = document.getElementById("register-btn");
  const profile = document.getElementById("profile-btn");
  const logout = document.getElementById("logout-btn");

  if (upload) {
    upload.onclick = (e) => {
      e.preventDefault();
      if (!isLoggedIn()) return openModal("login-modal");
      openModal("upload-modal");
    };
  }

  if (login) login.onclick = (e) => { e.preventDefault(); openModal("login-modal"); };
  if (register) register.onclick = (e) => { e.preventDefault(); openModal("register-modal"); };

  if (profile) {
    profile.onclick = (e) => {
      e.preventDefault();
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      document.getElementById("profile-username").value = user.username || "";
      document.getElementById("profile-country").value = user.country_code || "";
      openModal("profile-modal");
    };
  }

  if (logout) {
    logout.onclick = (e) => {
      e.preventDefault();
      logoutNow();
    };
  }
}

// =================== COUNTRIES ===================
async function loadCountries() {
  try {
    const res = await fetch(`${API_BASE}/api/countries`);
    const countries = await res.json();

    const selects = [
      document.getElementById("register-country"),
      document.getElementById("profile-country")
    ];

    selects.forEach(select => {
      if (!select) return;
      select.innerHTML = `<option value="">Country</option>`;
      countries.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.code;
        opt.textContent = c.name;
        select.appendChild(opt);
      });
    });
  } catch (err) {
    console.error("Failed to load countries", err);
  }
}

// =================== AUTH FORMS ===================
document.getElementById("login-form").addEventListener("submit", async e => {
  e.preventDefault();

  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;

  const res = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "Login failed");
    return;
  }

  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));

  closeModals();
  updateTopNav();
});

document.getElementById("register-form").addEventListener("submit", async e => {
  e.preventDefault();

  const username = document.getElementById("register-username").value.trim();
  const password = document.getElementById("register-password").value;
  const country_code = document.getElementById("register-country").value || null;

  const res = await fetch(`${API_BASE}/api/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, country_code })
  });

  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "Registration failed");
    return;
  }

  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("user", JSON.stringify(data.user));

  closeModals();
  updateTopNav();
});

document.getElementById("profile-form").addEventListener("submit", async e => {
  e.preventDefault();
  if (!isLoggedIn()) return;

  const country_code = document.getElementById("profile-country").value || null;

  const res = await fetch(`${API_BASE}/api/me`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ country_code })
  });

  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "Update failed");
    return;
  }

  // keep local user in sync
  localStorage.setItem("user", JSON.stringify(data));
  closeModals();
  updateTopNav();
});

// =================== UPLOAD FORM (multipart + JWT) ===================
document.getElementById("upload-form").addEventListener("submit", async e => {
  e.preventDefault();
  if (!isLoggedIn()) {
    alert("You must be logged in to upload.");
    return;
  }

  const fd = new FormData();
  fd.append("course_key", document.getElementById("upload-course").value);
  fd.append("machine_name", document.getElementById("upload-machine").value);
  fd.append("character_name", document.getElementById("upload-character").value);
  fd.append("time", document.getElementById("upload-time").value);

  const lap1 = document.getElementById("upload-lap1").value;
  const lap2 = document.getElementById("upload-lap2").value;
  const lap3 = document.getElementById("upload-lap3").value;
  if (lap1) fd.append("lap1", lap1);
  if (lap2) fd.append("lap2", lap2);
  if (lap3) fd.append("lap3", lap3);

  const proof = document.getElementById("upload-proof").files[0];
  if (!proof) {
    alert("Proof file required (video or screenshot).");
    return;
  }
  fd.append("proof", proof);

  const res = await fetch(`${API_BASE}/api/records`, {
    method: "POST",
    headers: authHeaders(), // JWT only; no content-type for FormData
    body: fd
  });

  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "Upload failed");
    return;
  }

  alert("Record submitted successfully!");
  closeModals();
});

// =================== VIEW SWITCHING ===================
const panels = document.querySelectorAll('.course-panel');
const courseLinks = document.querySelectorAll('.course-link');
const homeLinks = document.querySelectorAll('[data-view="home"]');

const courseTitle = document.getElementById('course-title');
const courseNote = document.getElementById('course-note');
const currentWrsBody = document.getElementById('current-wrs-body');
const statsByPlayerBody = document.getElementById('stats-by-player');
const statsByMachineBody = document.getElementById('stats-by-machine');
const statsByNationBody = document.getElementById('stats-by-nation');
const courseSummary = document.getElementById('course-summary');
const courseMap = document.getElementById('course-map');
const historyBody = document.getElementById('history-body');

function showView(viewName) {
  panels.forEach(panel =>
    panel.classList.toggle('active', panel.dataset.view === viewName)
  );
}

function setActiveCourseLink(courseId) {
  courseLinks.forEach(link => {
    link.classList.toggle('course-link-active', link.dataset.courseId === courseId);
  });
}

// =================== COURSE FETCH (from backend) ===================
async function loadCourse(courseId) {
  try {
    const res = await fetch(`${API_BASE}/api/course/${courseId}`);
    const data = await res.json();

    if (!res.ok) {
      courseTitle.textContent = "Coming soon";
      courseNote.textContent = data.error || "No data available yet.";
      currentWrsBody.innerHTML = "";
      historyBody.innerHTML = "";
      return;
    }

    renderCourse(data);
  } catch (err) {
    console.error(err);
    courseTitle.textContent = "Error";
    courseNote.textContent = "Backend not reachable.";
  }
}

function renderCourse(data) {
  courseTitle.textContent = data.name;
  courseNote.textContent = "One record per machine for " + data.name + ".";

  currentWrsBody.innerHTML = "";
  data.currentMachineWrs.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="machine-cell">
        <img src="${row.machineIcon}" alt="${row.machineName}" class="machine-icon">
        <span>${row.machineName}</span>
      </td>
      <td>${row.date}</td>
      <td>${row.time}</td>
      <td>${row.player}</td>
      <td><img src="images/country-flags-main/svg/${row.nationCode}.svg" class="flag" alt=""></td>
      <td>${row.days ?? 0}</td>
      <td>${row.lap1 ?? ""}</td>
      <td>${row.lap2 ?? ""}</td>
      <td>${row.lap3 ?? ""}</td>
      <td><img src="${row.charIcon}" alt="${row.charAlt}" class="char-icon"></td>
    `;
    currentWrsBody.appendChild(tr);
  });

  // summary
  const sum = data.summary || {};
  courseSummary.innerHTML = `
    <li><strong>Total WRs:</strong> ${sum.totalMachineWrs ?? 0}</li>
    <li><strong>Unique Players:</strong> ${sum.uniquePlayers ?? 0}</li>
    <li><strong>Unique Nations:</strong> ${sum.uniqueNations ?? 0}</li>
    <li><strong>Machines:</strong> ${sum.uniqueMachines ?? 0}</li>
  `;

  // map icon
  courseMap.src = data.mapIcon ? data.mapIcon : "";
  courseMap.alt = data.name;

  // history
  historyBody.innerHTML = (data.history || []).map(h => `
    <tr>
      <td>${h.date}</td>
      <td class="machine-cell">
        <img src="${h.machineIcon}" class="machine-icon" alt="">
        <span>${h.machineName}</span>
      </td>
      <td>${h.time}</td>
      <td>${h.player}</td>
      <td><img src="images/country-flags-main/svg/${h.nationCode}.svg" class="flag" alt=""></td>
      <td>${h.days ?? 0}</td>
      <td>${h.lap1 ?? ""}</td>
      <td>${h.lap2 ?? ""}</td>
      <td>${h.lap3 ?? ""}</td>
      <td><img src="${h.charIcon}" class="char-icon" alt=""></td>
    </tr>
  `).join("");
}

// =================== SIDEBAR HANDLERS ===================
courseLinks.forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    const courseId = link.dataset.courseId;
    setActiveCourseLink(courseId);
    loadCourse(courseId);
    showView("course");
  });
});

homeLinks.forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    setActiveCourseLink(null);
    showView("home");
  });
});

// =================== INIT ===================
showView("home");
updateTopNav();
loadCountries();
