// =================== CONFIG ===================
const API_BASE = "http://127.0.0.1:5000"; // Backend API base URL
const STATIC_BASE = "static";

// =================== UTIL ===================
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

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

function normalizeCountryCode(code) {
  if (!code) return "us";
  const s = String(code).toLowerCase().trim();
  if (s === "0" || s.length < 2) return "us";
  return s.slice(0, 2);
}

function flagSrc(code) {
  const c = normalizeCountryCode(code);
  return `${STATIC_BASE}/images/country-flags-main/svg/${c}.svg`;
}

function safeStaticPath(p) {
  if (!p) return "";
  const pp = String(p).replaceAll("\\", "/").trim();
  if (pp.startsWith("http://") || pp.startsWith("https://") || pp.startsWith("/")) return pp;
  if (pp.startsWith("static/")) return pp;
  return `${STATIC_BASE}/${pp}`;
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

// =================== MODALS ===================
function openModal(id) {
  document.getElementById(id)?.classList.add("active");
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
      scrollToTop();
      if (!isLoggedIn()) return openModal("login-modal");
      openModal("upload-modal");
    };
  }

  if (login) login.onclick = (e) => { e.preventDefault(); scrollToTop(); openModal("login-modal"); };

  if (register) register.onclick = (e) => {
    e.preventDefault();
    scrollToTop();
    openModal("register-modal");
    loadCountries();
  };

  if (profile) {
    profile.onclick = (e) => {
      e.preventDefault();
      scrollToTop();
      const user = JSON.parse(localStorage.getItem("user") || "{}");
      document.getElementById("profile-username").value = user.username || "";
      openModal("profile-modal");
      loadCountries().then(() => {
        document.getElementById("profile-country").value = (user.country_code || "").toLowerCase();
      });
    };
  }

  if (logout) {
    logout.onclick = (e) => {
      e.preventDefault();
      scrollToTop();
      logoutNow();
    };
  }
}

// =================== COUNTRIES ===================
async function loadCountries() {
  try {
    const countries = await fetchJSON(`${API_BASE}/api/countries`);
    const selects = [
      document.getElementById("register-country"),
      document.getElementById("profile-country")
    ];
    selects.forEach(select => {
      if (!select) return;
      select.innerHTML = `<option value="">Country</option>`;
      countries.forEach(c => {
        const opt = document.createElement("option");
        opt.value = (c.code || "").toLowerCase();
        opt.textContent = c.name;
        select.appendChild(opt);
      });
    });
  } catch (err) {
    console.error("Failed to load countries", err);
  }
}

// =================== AUTH FORMS ===================
document.getElementById("login-form")?.addEventListener("submit", async e => {
  e.preventDefault();

  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const data = await fetchJSON(`${API_BASE}/api/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    closeModals();
    updateTopNav();
  } catch (err) {
    alert(err.message || "Login failed");
  }
});


// this registers the user, along with their passwd and country
document.getElementById("register-form")?.addEventListener("submit", async e => {
  e.preventDefault();

  const username = document.getElementById("register-username").value.trim();
  const password = document.getElementById("register-password").value;
  const country_code = document.getElementById("register-country").value || null;

  try {
    const data = await fetchJSON(`${API_BASE}/api/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, country_code })
    });

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    closeModals();
    updateTopNav();
  } catch (err) {
    alert(err.message || "Registration failed");
  }
});


//This part is updating the country of the user
document.getElementById("profile-form")?.addEventListener("submit", async e => {
  e.preventDefault();
  if (!isLoggedIn()) return;

  let val = document.getElementById("profile-country").value;

  let country_code = (val && val.trim() !== "") ? val.toLowerCase() : null;

  if (!country_code || country_code === "") {
      country_code = null;
  }


  try {
    const data = await fetchJSON(`${API_BASE}/api/me`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ country_code })
    });

    localStorage.setItem("user", JSON.stringify(data));
    alert("Profile Updated");
    closeModals();
    updateTopNav();
  } catch (err) {
    console.error("Validation Error:", err);
    alert(err.message || "Update failed");
  }
});

// =================== UPLOAD FORM (multipart + JWT) ===================
function isValidTimeFormat(timeStr) {
    // Regex for: minutes'seconds"milliseconds (e.g., 1'05"780)
    const regex = /^\d+'\d{2}"\d{3}$/;
    return regex.test(timeStr);
}

document.getElementById("upload-form")?.addEventListener("submit", async e => {
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

  //error check on time input
  const timeInput = document.getElementById("upload-time").value.trim();

  if (!isValidTimeFormat(timeInput)) {
      alert("Invalid time format! Please use: Minutes'Seconds\"Milliseconds (Ex: 1'05\"780)");
      return;
  }

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

  

  try {
    await fetchJSON(`${API_BASE}/api/records`, {
      method: "POST",
      headers: authHeaders(), // JWT only
      body: fd
    });

    alert("Record submitted successfully!");
    closeModals();

    // refresh the main stats pages
    loadHomeCurrentWrs();
    loadRecentWrs();
  } catch (err) {
    alert(err.message || "Upload failed");
  }
});

// =================== VIEW SWITCHING ===================
const panels = document.querySelectorAll(".course-panel");
const courseLinks = document.querySelectorAll(".course-link");
const navLinks = document.querySelectorAll(".nav-link[data-view]");
const logoLink = document.querySelector(".logo-link[data-view]");

// Course panel DOM
const courseTitle = document.getElementById("course-title");
const courseNote = document.getElementById("course-note");
const currentWrsBody = document.getElementById("current-wrs-body");
const courseSummary = document.getElementById("course-summary");
const courseMap = document.getElementById("course-map");
const historyBody = document.getElementById("history-body");

// Course stats DOM (these were missing -> made the boxes blank)
const statsByPlayerBody = document.getElementById("stats-by-player");
const statsByMachineBody = document.getElementById("stats-by-machine");
const statsByNationBody = document.getElementById("stats-by-nation");

function showView(viewName) {
  panels.forEach(panel =>
    panel.classList.toggle("active", panel.dataset.view === viewName)
  );
}

function setActiveCourseLink(courseId) {
  courseLinks.forEach(link => {
    link.classList.toggle("course-link-active", link.dataset.courseId === courseId);
  });
}

// =================== STATS PAGE LOADERS ===================
async function loadHomeCurrentWrs() {
  const tbody = document.getElementById("home-current-wrs-body");
  if (!tbody) return;

  try {
    const rows = await fetchJSON(`${API_BASE}/api/current-wrs`);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.course_name}</td>
        <td class="machine-cell">
          <img src="${safeStaticPath(r.machine_icon)}" class="machine-icon" alt="">
          <span>${r.machine_name}</span>
        </td>
        <td>${r.time}</td>
        <td>${r.player}</td>
        <td><img src="${flagSrc(r.nation_code)}" class="flag" alt=""></td>
        <td>${r.date || ""}</td>
        <td><img src="${safeStaticPath(r.char_icon)}" class="char-icon" alt=""></td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML = "";
  }
}

async function loadSnapshot() {
  const tbody = document.getElementById("snapshot-body");
  if (!tbody) return;

  try {
    const rows = await fetchJSON(`${API_BASE}/api/wr-snapshot`);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.course_name}</td>
        <td class="machine-cell">
          <img src="${safeStaticPath(r.machine_icon)}" class="machine-icon" alt="">
          <span>${r.machine_name}</span>
        </td>
        <td>${r.time}</td>
        <td>${r.player}</td>
        <td><img src="${flagSrc(r.nation_code)}" class="flag" alt=""></td>
        <td>${r.date || ""}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML = "";
  }
}

async function loadPlayerRankings() {
  const tbody = document.getElementById("player-rankings-body");
  if (!tbody) return;

  try {
    const rows = await fetchJSON(`${API_BASE}/api/rankings/players`);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.rank}</td>
        <td>${r.player}</td>
        <td><img src="${flagSrc(r.nation_code)}" class="flag" alt=""></td>
        <td>${r.wr_count}</td>
        <td>${r.total_wr_days}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML = "";
  }
}

async function loadCountryRankings() {
  const tbody = document.getElementById("country-rankings-body");
  if (!tbody) return;

  try {
    const rows = await fetchJSON(`${API_BASE}/api/rankings/countries`);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.rank}</td>
        <td><img src="${flagSrc(r.nation_code)}" class="flag" alt=""></td>
        <td>${r.wr_count}</td>
        <td>${r.unique_players}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML = "";
  }
}

async function loadRecentWrs() {
  const tbody = document.getElementById("recent-wrs-body");
  if (!tbody) return;

  try {
    const rows = await fetchJSON(`${API_BASE}/api/recent-wrs?days=5`);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.date || ""}</td>
        <td>${r.course_name}</td>
        <td class="machine-cell">
          <img src="${safeStaticPath(r.machine_icon)}" class="machine-icon" alt="">
          <span>${r.machine_name}</span>
        </td>
        <td>${r.time}</td>
        <td>${r.player}</td>
        <td><img src="${flagSrc(r.nation_code)}" class="flag" alt=""></td>
        <td><img src="${safeStaticPath(r.char_icon)}" class="char-icon" alt=""></td>
      </tr>
    `).join("");
  } catch (err) {
    console.error(err);
    tbody.innerHTML = "";
  }
}

// =================== COURSE FETCH (from backend) ===================
async function loadCourse(courseId) {
  try {
    const data = await fetchJSON(`${API_BASE}/api/course/${courseId}`);
    renderCourse(data);
  } catch (err) {
    console.error(err);
    courseTitle.textContent = "Error";
    courseNote.textContent = "No data available yet.";
    currentWrsBody.innerHTML = "";
    historyBody.innerHTML = "";
    if (statsByPlayerBody) statsByPlayerBody.innerHTML = "";
    if (statsByMachineBody) statsByMachineBody.innerHTML = "";
    if (statsByNationBody) statsByNationBody.innerHTML = "";
  }
}

function renderCourse(data) {
  courseTitle.textContent = data.name;
  courseNote.textContent = "One record per machine for " + data.name + ".";

  currentWrsBody.innerHTML = "";
  (data.currentMachineWrs || []).forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="machine-cell">
        <img src="${safeStaticPath(row.machineIcon)}" alt="${row.machineName}" class="machine-icon">
        <span>${row.machineName}</span>
      </td>
      <td>${row.date || ""}</td>
      <td>${row.time || ""}</td>
      <td>${row.player || ""}</td>
      <td><img src="${flagSrc(row.nationCode)}" class="flag" alt=""></td>
      <td>${row.days ?? 0}</td>
      <td>${row.lap1 ?? ""}</td>
      <td>${row.lap2 ?? ""}</td>
      <td>${row.lap3 ?? ""}</td>
      <td><img src="${safeStaticPath(row.charIcon)}" alt="" class="char-icon"></td>
    `;
    currentWrsBody.appendChild(tr);
  });

  const sum = data.summary || {};
  courseSummary.innerHTML = `
    <li><strong>Total WRs:</strong> ${sum.totalMachineWrs ?? 0}</li>
    <li><strong>Unique Players:</strong> ${sum.uniquePlayers ?? 0}</li>
    <li><strong>Unique Nations:</strong> ${sum.uniqueNations ?? 0}</li>
    <li><strong>Machines:</strong> ${sum.uniqueMachines ?? 0}</li>
  `;

  courseMap.src = safeStaticPath(data.mapIcon || "");
  courseMap.alt = data.name;

  // ===== CHANGES YOU REQUESTED =====
  const stats = data.stats || {};

  // 1) Remove / hide the Player stats section (body rows)
  if (statsByPlayerBody) {
    statsByPlayerBody.innerHTML = "";
    // Optional: hide the whole box visually (keeps layout clean)
    const playerBox = statsByPlayerBody.closest(".stat-box");
    if (playerBox) playerBox.style.display = "none";
  }

  // Build machine icon lookup so machine stats can show icons
  const machineIconByName = {};
  (data.currentMachineWrs || []).forEach(r => {
    if (r?.machineName && r?.machineIcon) machineIconByName[r.machineName] = r.machineIcon;
  });

  // 2) Machine stats table (unchanged)
  if (statsByMachineBody) {
    statsByMachineBody.innerHTML = (stats.byMachine || []).map(r => {
      const icon = machineIconByName[r.machine] || "";
      return `
        <tr>
          <td class="machine-cell">
            ${icon ? `<img src="${safeStaticPath(icon)}" class="machine-icon" alt="">` : ``}
            <span>${r.machine ?? ""}</span>
          </td>
          <td>${r.total ?? 0}</td>
          <td>${r.pct ?? 0}</td>
        </tr>
      `;
    }).join("");
  }

  
  if (statsByNationBody) {
    statsByNationBody.innerHTML = (stats.byNation || []).map(r => `
      <tr>
        <td><img src="${flagSrc(r.nation)}" class="flag" alt=""></td>
        <td>${r.count ?? 0}</td>
      </tr>
    `).join("");
  }

  // 4) Make the overall stats + map appear FIRST in the Course Stats row
  //    (This is the box containing #course-summary and #course-map)
  const statsRow = document.querySelector(".course-stats-row");
  const summaryBox = courseSummary?.closest(".stat-box");
  if (statsRow && summaryBox) {
    statsRow.prepend(summaryBox);
  }
  // ===== END CHANGES =====

  historyBody.innerHTML = (data.history || []).map(h => `
    <tr>
      <td>${h.date || ""}</td>
      <td class="machine-cell">
        <img src="${safeStaticPath(h.machineIcon)}" class="machine-icon" alt="">
        <span>${h.machineName || ""}</span>
      </td>
      <td>${h.time || ""}</td>
      <td>${h.player || ""}</td>
      <td><img src="${flagSrc(h.nationCode)}" class="flag" alt=""></td>
      <td>${h.days ?? 0}</td>
      <td>${h.lap1 ?? ""}</td>
      <td>${h.lap2 ?? ""}</td>
      <td>${h.lap3 ?? ""}</td>
      <td><img src="${safeStaticPath(h.charIcon)}" class="char-icon" alt=""></td>
    </tr>
  `).join("");
}


// =================== SIDEBAR HANDLERS ===================
// Stats nav links
navLinks.forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    const view = link.dataset.view;

    setActiveCourseLink(null);
    showView(view);
    scrollToTop();

    if (view === "home") loadHomeCurrentWrs();
    if (view === "snapshot") loadSnapshot();
    if (view === "player-rankings") loadPlayerRankings();
    if (view === "country-rankings") loadCountryRankings();
    if (view === "recent-wrs") loadRecentWrs();
  });
});

// Logo -> home
document.querySelector(".logo-link")?.addEventListener("click", e => {
  e.preventDefault();
  setActiveCourseLink(null);
  showView("home");
  scrollToTop();
  loadHomeCurrentWrs();
});

// Course links
courseLinks.forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    const courseId = link.dataset.courseId;
    setActiveCourseLink(courseId);
    loadCourse(courseId);
    showView("course");
    scrollToTop();
  });
});

// =================== INIT ===================
showView("home");
updateTopNav();
loadCountries();
loadHomeCurrentWrs();


//===================== user deletion ==========================

document.getElementById("delete-account-btn")?.addEventListener("click", async () => {
  const confirmed = confirm("Are you sure you want to delete your AirRiders account? This will wipe your records and stats forever!");
  
  if (!confirmed) return;

  try {
    await fetchJSON(`${API_BASE}/api/me`, {
      method: "DELETE",
      headers: authHeaders()
    });

    alert("Your account has been deleted.");
    
    // Clears local storage
    logoutNow(); 
    closeModals();
    showView("home"); 
    
  } catch (err) {
    alert(err.message || "Deletion failed. Please try again.");
  }
});