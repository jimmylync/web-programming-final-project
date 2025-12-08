// ========== PANEL SWITCHING ==========
const panels = document.querySelectorAll('.course-panel');
const courseLinks = document.querySelectorAll('.course-link');
const homeLinks = document.querySelectorAll('[data-view="home"]');

// Target elements for course view
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

// ========== EXAMPLE DATA (replace later with database/API) ==========
//
// Four example courses:
//   - floria-fields (Warp Star & Kirby)
//   - waveflow-waters (Rex Wheelie & Marx)
//   - flower (Bull Tank & Taranza)
//   - flow (Hop Star & Meta Knight)
//

const exampleCourseData = {
  "floria-fields": {
    name: "Floria Fields",
    mapIcon: "images/mapICONS/Floria_Fields.png",
    summary: {
      totalMachineWrs: 18,
      uniquePlayers: 7,
      uniqueNations: 4,
      uniqueMachines: 18
    },
    currentMachineWrs: [
      {
        machineName: "Warp Star",
        machineIcon: "images/machineICONS/KARs_Warp_Star_Icon.png",
        date: "2025-09-12",
        time: "1'12\"501",
        player: "petal",
        nationCode: "us",
        days: 20,
        lap1: 23.5,
        lap2: 24.0,
        lap3: 25.0,
        charIcon: "images/charICONS/KARs_Kirby_icon.png",
        charAlt: "Kirby"
      }
    ],
    statsByPlayer: [
      { player: "petal", days: 20, percent: 55 }
    ],
    statsByMachine: [
      { machine: "Warp Star", days: 20, percent: 55 }
    ],
    statsByNation: [
      { nation: "USA", wrs: 10 }
    ],
    history: [
      {
        date: "2025-09-01",
        machineName: "Warp Star",
        machineIcon: "images/machineICONS/KARs_Warp_Star_Icon.png",
        time: "1'13\"000",
        player: "petal",
        nationCode: "us",
        days: 1,
        lap1: 24.0,
        lap2: 24.5,
        lap3: 24.5,
        charIcon: "images/charICONS/KARs_Kirby_icon.png",
        charAlt: "Kirby"
      }
    ]
  },

  "waveflow-waters": {
    name: "Waveflow Waters",
    mapIcon: "images/mapICONS/Waveflow_Waters.png",
    summary: {
      totalMachineWrs: 18,
      uniquePlayers: 4,
      uniqueNations: 3,
      uniqueMachines: 18
    },
    currentMachineWrs: [
      {
        machineName: "Rex Wheelie",
        machineIcon: "images/machineICONS/KARs_Rex_Wheelie_Icon.png",
        date: "2025-08-02",
        time: "1'05\"780",
        player: "tsunami",
        nationCode: "jp",
        days: 32,
        lap1: 21.0,
        lap2: 22.5,
        lap3: 22.2,
        charIcon: "images/charICONS/KARs_Marx_icon.png",
        charAlt: "Marx"
      }
    ],
    statsByPlayer: [
      { player: "tsunami", days: 32, percent: 70 }
    ],
    statsByMachine: [
      { machine: "Rex Wheelie", days: 32, percent: 70 }
    ],
    statsByNation: [
      { nation: "Japan", wrs: 14 }
    ],
    history: []
  },

  // Top Ride example 1: Flower
  "flower": {
    name: "Flower (Top Ride)",
    mapIcon: "images/mapICONS/Flower.png",
    summary: {
      totalMachineWrs: 8,
      uniquePlayers: 3,
      uniqueNations: 3,
      uniqueMachines: 8
    },
    currentMachineWrs: [
      {
        machineName: "Bull Tank",
        machineIcon: "images/machineICONS/KARs_Bull_Tank_Icon.png",
        date: "2025-03-04",
        time: "0'32\"120",
        player: "blossom",
        nationCode: "ca",
        days: 50,
        lap1: 10.3,
        lap2: 10.1,
        lap3: 11.7,
        charIcon: "images/charICONS/KARs_Taranza_icon.png",
        charAlt: "Taranza"
      }
    ],
    statsByPlayer: [
      { player: "blossom", days: 50, percent: 80 }
    ],
    statsByMachine: [
      { machine: "Bull Tank", days: 50, percent: 80 }
    ],
    statsByNation: [
      { nation: "Canada", wrs: 8 }
    ],
    history: []
  },

  // Top Ride example 2: Flow
  "flow": {
    name: "Flow (Top Ride)",
    mapIcon: "images/mapICONS/Flow.png",
    summary: {
      totalMachineWrs: 8,
      uniquePlayers: 2,
      uniqueNations: 2,
      uniqueMachines: 8
    },
    currentMachineWrs: [
      {
        machineName: "Hop Star",
        machineIcon: "images/machineICONS/KARs_Hop_Star_Icon.png",
        date: "2025-01-20",
        time: "0'29\"800",
        player: "river",
        nationCode: "us",
        days: 10,
        lap1: 9.1,
        lap2: 9.4,
        lap3: 11.3,
        charIcon: "images/charICONS/KARs_Meta_Knight_icon.png",
        charAlt: "Meta Knight"
      }
    ],
    statsByPlayer: [
      { player: "river", days: 10, percent: 60 }
    ],
    statsByMachine: [
      { machine: "Hop Star", days: 10, percent: 60 }
    ],
    statsByNation: [
      { nation: "USA", wrs: 6 }
    ],
    history: []
  }
};

// ========== DYNAMIC RENDERING ==========

function renderCourse(data) {
  courseTitle.textContent = data.name;
  courseNote.textContent = "One record per machine for " + data.name + ".";

  // Current WR table
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
      <td>
        <img src="images/country-flags-main/svg/${row.nationCode}.svg"
             alt="${row.nationCode.toUpperCase()}"
             class="flag">
      </td>
      <td>${row.days}</td>
      <td>${row.lap1}</td>
      <td>${row.lap2}</td>
      <td>${row.lap3}</td>
      <td>
        <img src="${row.charIcon}" alt="${row.charAlt}" class="char-icon">
      </td>
    `;
    currentWrsBody.appendChild(tr);
  });

  // Stats (three boxes)
  statsByPlayerBody.innerHTML = data.statsByPlayer
    .map(s => `<tr><td>${s.player}</td><td>${s.days}</td><td>${s.percent}</td></tr>`)
    .join("");

  statsByMachineBody.innerHTML = data.statsByMachine
    .map(s => `<tr><td>${s.machine}</td><td>${s.days}</td><td>${s.percent}</td></tr>`)
    .join("");

  statsByNationBody.innerHTML = data.statsByNation
    .map(s => `<tr><td>${s.nation}</td><td>${s.wrs}</td></tr>`)
    .join("");

  // Summary + Map
  const sum = data.summary;
  courseSummary.innerHTML = `
    <li><strong>Total WRs:</strong> ${sum.totalMachineWrs}</li>
    <li><strong>Unique Players:</strong> ${sum.uniquePlayers}</li>
    <li><strong>Unique Nations:</strong> ${sum.uniqueNations}</li>
    <li><strong>Machines:</strong> ${sum.uniqueMachines}</li>
  `;
  courseMap.src = data.mapIcon;
  courseMap.alt = data.name;

  // History (optional)
  historyBody.innerHTML = data.history
    .map(h => `
      <tr>
        <td>${h.date}</td>
        <td class="machine-cell">
          <img src="${h.machineIcon}" alt="${h.machineName}" class="machine-icon">
          <span>${h.machineName}</span>
        </td>
        <td>${h.time}</td>
        <td>${h.player}</td>
        <td>
          <img src="images/country-flags-main/svg/${h.nationCode}.svg"
               alt="${h.nationCode.toUpperCase()}"
               class="flag">
        </td>
        <td>${h.days}</td>
        <td>${h.lap1}</td>
        <td>${h.lap2}</td>
        <td>${h.lap3}</td>
        <td>
          <img src="${h.charIcon}" alt="${h.charAlt}" class="char-icon">
        </td>
      </tr>
    `)
    .join("");
}

// Load course by ID
async function loadCourse(courseId) {
  // later this can be a real API call:
  // const res = await fetch(`/api/courses/${courseId}`);
  // const data = await res.json();

  const data = exampleCourseData[courseId];
  if (!data) {
    courseTitle.textContent = "Coming soon";
    courseNote.textContent = "No data available yet for this course.";
    currentWrsBody.innerHTML = "";
    statsByPlayerBody.innerHTML = "";
    statsByMachineBody.innerHTML = "";
    statsByNationBody.innerHTML = "";
    courseSummary.innerHTML = "";
    courseMap.src = "";
    courseMap.alt = "";
    historyBody.innerHTML = "";
    return;
  }

  renderCourse(data);
}

// Event handlers
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

// Default panel
showView("home");
