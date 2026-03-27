// ─── i18n ────────────────────────────────────────────────────────────────────

const STRINGS = {
  sv: {
    title:            "3 dialoger (sv, längd 100–500)",
    btnNext:          (n) => `Auto-sammanfattning (${n} msg)`,
    btnFull:          "Skanna till slut",
    btnReset:         "Återställ sammanfattning",
    btnPrompts:       "Promptar",
    btnSave:          "Spara",
    btnClose:         "← Tillbaka",
    btnResetPrompts:  "Återställ standard",
    headMessages:     "Meddelanden",
    headSummaryJson:  "Sammanfattning JSON",
    headProgress:     "Chattförlopp",
    modalTitle:       "Grok-promptar",
    labelSystem:      "Systemprompt",
    labelUser:        "Användarprompt-mall",
    promptHint:       "Platshållare: {previous_summary}, {new_messages}, {lang}",
    loading:          (id) => `Laddar dialog #${id}…`,
    noDialogues:      "Inga lämpliga dialoger hittades.",
    loadError:        (msg) => `Laddningsfel: ${msg}`,
    summaryUpdating:  "Uppdaterar sammanfattning…",
    summaryError:     (msg) => `Sammanfattningsfel: ${msg}`,
    resetError:       (msg) => `Återställningsfel: ${msg}`,
    scanStep:         (n) => `Skannar till slut… steg ${n}`,
    scanDone:         (s) => `Klar: #${s.dialogue_id}, bearbetat ${s.processed_messages}/${s.total_messages}`,
    scanError:        (msg) => `Skanningsfel: ${msg}`,
    promptsSaved:     "Promptar sparade.",
    shownFirst:       (n, total) => `Visar första ${n} av ${total} meddelanden.`,
    shownAll:         (n) => `Visar alla ${n} meddelanden.`,
    noData:           "Inga data",
    noSummary:        "Inga sammanfattningsdata.",
    facts:            "fakta",
    translating:      "",
    labelFemale:      "Female",
    labelMale:        "Male",
    labelUser:        "User",
    labelPersona:     "Persona",
    catPersonal:      "Personlig",
    catRelationship:  "Relation",
    catWork:          "Arbete",
    catLifestyle:     "Livsstil",
    catSexual:        "Sexuell",
    catPersonality:   "Personlighet",
  },
  ru: {
    title:            "3 диалога (sv, длина 100–500)",
    btnNext:          (n) => `Авто summary (${n} сообщений)`,
    btnFull:          "Скан до конца",
    btnReset:         "Сброс summary",
    btnPrompts:       "Промпты",
    btnSave:          "Сохранить",
    btnClose:         "← Назад",
    btnResetPrompts:  "Сбросить на дефолт",
    headMessages:     "Сообщения",
    headSummaryJson:  "Summary JSON",
    headProgress:     "Прогресс по чатам",
    modalTitle:       "Промпты для Grok",
    labelSystem:      "System prompt",
    labelUser:        "User prompt шаблон",
    promptHint:       "Плейсхолдеры: {previous_summary}, {new_messages}, {lang}",
    noDialogues:      "Не найдено подходящих диалогов.",
    loadError:        (msg) => `Ошибка загрузки: ${msg}`,
    summaryUpdating:  "Обновляю summary…",
    summaryError:     (msg) => `Ошибка summary: ${msg}`,
    resetError:       (msg) => `Ошибка reset: ${msg}`,
    scanStep:         (n) => `Сканирую диалог до конца… шаг ${n}`,
    scanDone:         (s) => `Готово: #${s.dialogue_id}, обработано ${s.processed_messages}/${s.total_messages}`,
    scanError:        (msg) => `Ошибка скана: ${msg}`,
    promptsSaved:     "Промпты сохранены.",
    shownFirst:       (n, total) => `Показаны первые ${n} из ${total} сообщений.`,
    shownAll:         (n) => `Показаны все ${n} сообщений.`,
    noData:           "Нет данных",
    noSummary:        "Нет данных по summary.",
    facts:            "факты",
    translating:      "Перевод ещё не готов — отображается оригинал (sv).",
    labelFemale:      "Female",
    labelMale:        "Male",
    labelUser:        "User",
    labelPersona:     "Persona",
    catPersonal:      "Personal",
    catRelationship:  "Relationship",
    catWork:          "Work",
    catLifestyle:     "Lifestyle",
    catSexual:        "Sexual",
    catPersonality:   "Personality",
  },
  en: {
    title:            "3 dialogues (sv, length 100–500)",
    btnNext:          (n) => `Auto summary (${n} msgs)`,
    btnFull:          "Scan to end",
    btnReset:         "Reset summary",
    btnPrompts:       "Prompts",
    btnSave:          "Save",
    btnClose:         "← Back",
    btnResetPrompts:  "Reset to default",
    headMessages:     "Messages",
    headSummaryJson:  "Summary JSON",
    headProgress:     "Chat progress",
    modalTitle:       "Grok prompts",
    labelSystem:      "System prompt",
    labelUser:        "User prompt template",
    promptHint:       "Placeholders: {previous_summary}, {new_messages}, {lang}",
    loading:          (id) => `Loading dialogue #${id}…`,
    noDialogues:      "No suitable dialogues found.",
    loadError:        (msg) => `Load error: ${msg}`,
    summaryUpdating:  "Updating summary…",
    summaryError:     (msg) => `Summary error: ${msg}`,
    resetError:       (msg) => `Reset error: ${msg}`,
    scanStep:         (n) => `Scanning to end… step ${n}`,
    scanDone:         (s) => `Done: #${s.dialogue_id}, processed ${s.processed_messages}/${s.total_messages}`,
    scanError:        (msg) => `Scan error: ${msg}`,
    promptsSaved:     "Prompts saved.",
    shownFirst:       (n, total) => `Showing first ${n} of ${total} messages.`,
    shownAll:         (n) => `Showing all ${n} messages.`,
    noData:           "No data",
    noSummary:        "No summary data.",
    facts:            "facts",
    translating:      "Translation not ready yet — showing original (sv).",
    labelFemale:      "Female",
    labelMale:        "Male",
    labelUser:        "User",
    labelPersona:     "Persona",
    catPersonal:      "Personal",
    catRelationship:  "Relationship",
    catWork:          "Work",
    catLifestyle:     "Lifestyle",
    catSexual:        "Sexual",
    catPersonality:   "Personality",
  },
};

function getCookie(name) {
  const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return m ? m.pop() : null;
}

let currentLang = getCookie("chat_lang") || localStorage.getItem("lang") || "ru";
let chunkSize = 10; // updated from /api/status on init

function t(key, ...args) {
  const entry = STRINGS[currentLang]?.[key] ?? STRINGS["en"]?.[key] ?? key;
  return typeof entry === "function" ? entry(...args) : entry;
}

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key === "btnNext") {
      el.textContent = t("btnNext", chunkSize);
    } else {
      const val = t(key);
      if (typeof val === "string") el.textContent = val;
    }
  });
  // Update lang buttons active state
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === currentLang);
  });
}

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem("lang", lang);
  document.cookie = "chat_lang=" + lang + "; path=/; max-age=" + (365 * 24 * 3600);
  applyI18n();
  if (activeDialogueId) {
    selectDialogue(activeDialogueId);
  }
  renderSummaryOverview(lastOverviewStates);
}

// ─── DOM refs ─────────────────────────────────────────────────────────────────

const tabsEl              = document.getElementById("tabs");
const messagesEl          = document.getElementById("messages");
const summaryEl           = document.getElementById("summary");
const statusEl            = document.getElementById("status");
const btnSummaryNext      = document.getElementById("btn-summary-next");
const btnSummaryFull      = document.getElementById("btn-summary-full");
const btnSummaryReset     = document.getElementById("btn-summary-reset");
const systemPromptEl      = null; // prompts are on prompts.php
const userPromptEl        = null;
const messagesMetaEl      = document.getElementById("messages-meta");
const summaryOverviewEl   = document.getElementById("summary-overview");
const summaryFactsEl      = document.getElementById("summary-facts");
const mainViewEl          = document.getElementById("main-view");
const promptsViewEl       = null;

const MESSAGES_PREVIEW_LIMIT = 300;
let isBusy = false;
let dialogues = [];
let activeDialogueId = null;
let lastOverviewStates = [];

// ─── Default prompts ──────────────────────────────────────────────────────────

const DEFAULT_SYSTEM_PROMPT = `You are an intelligence analyst building a factual profile of a person from a chat conversation.
Your goal is NOT to summarize the conversation — your goal is to EXTRACT specific facts.

Return ONLY valid JSON with the exact schema provided in the system instructions.

WHAT TO LOOK FOR in each category:
- identity: name, age, city, country, contact handles (phone, kik, telegram, email)
- work_money: job title, employer, income level, financial situation, debts
- lifestyle: living situation (alone/family), daily schedule, hobbies, interests
- relationship: marital status, partner, ex-partners, children, family situation
- sexual: expressed desires, preferences, boundaries, orientation
- personality: emotional state, communication style, red flags, manipulation tactics

Language: {lang}

Rules:
- Only record facts explicitly stated or strongly implied — no guessing.
- Preserve existing facts unless directly contradicted.
- Each category = max 1-2 concise facts. No long prose.
- identity.gender must be a single word: female or male.
- Skip a category entirely if nothing is known — use empty object.
- Respond with pure JSON only.`;

const DEFAULT_USER_PROMPT = `Extract and update profile facts from the new messages below.
Focus on finding real facts about the client: family, work, location, finances, relationships.

previous_summary:
{previous_summary}

new_messages:
{new_messages}`;

// ─── Utilities ────────────────────────────────────────────────────────────────

function hasRequiredDom() {
  return Boolean(tabsEl && messagesEl && summaryEl && statusEl && summaryFactsEl);
}

function setStatus(text, isError = false) {
  if (!statusEl) return;
  statusEl.textContent = text;
  statusEl.style.color = isError ? "#b91c1c" : "#374151";
}

function setBusy(nextDisabled = true) {
  isBusy = nextDisabled;
  if (btnSummaryNext) btnSummaryNext.disabled = nextDisabled;
  if (btnSummaryFull) btnSummaryFull.disabled = nextDisabled;
  if (btnSummaryReset) btnSummaryReset.disabled = nextDisabled;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status}: ${text}`);
  }
  return response.json();
}

// ─── Render ───────────────────────────────────────────────────────────────────

function renderTabs() {
  if (!tabsEl) return;
  tabsEl.innerHTML = "";
  for (const d of dialogues) {
    const btn = document.createElement("button");
    btn.className = `tab ${d.dialogue_id === activeDialogueId ? "active" : ""}`;

    const state = lastOverviewStates.find((s) => s.dialogue_id === d.dialogue_id);
    const pct = state && state.total_messages
      ? Math.round((state.processed_messages / state.total_messages) * 100)
      : 0;
    const facts = state ? (state.fact_count || 0) : 0;

    btn.innerHTML = `
      <div class="tab-title">#${d.dialogue_id}</div>
      <div class="tab-meta">${d.dialogue_length_messages} msgs · ${pct}% · ${facts} ${t("facts")}</div>
    `;
    btn.onclick = () => selectDialogue(d.dialogue_id);
    tabsEl.appendChild(btn);
  }
}

function renderMessages(messages, showTranslationNote = false) {
  if (!messagesEl) return;
  messagesEl.innerHTML = "";
  if (showTranslationNote) {
    const note = document.createElement("p");
    note.className = "hint";
    note.textContent = t("translating");
    messagesEl.appendChild(note);
  }
  if (!Array.isArray(messages)) return;
  for (const m of messages) {
    const row = document.createElement("div");
    row.className = "message-row";
    row.innerHTML = `<div class="meta">#${m.msg_order} | ${m.sender_gender}</div><div class="text"></div>`;
    row.querySelector(".text").textContent = m.message;
    messagesEl.appendChild(row);
  }
}

function renderSummary(state) {
  if (!summaryEl) return;
  summaryEl.textContent = JSON.stringify(state.summary, null, 2);
  const pct = state.total_messages
    ? Math.round((state.processed_messages / state.total_messages) * 100)
    : 0;
  setStatus(`#${state.dialogue_id} | ${state.processed_messages}/${state.total_messages} (${pct}%)`);
  renderSummaryFacts(state.summary);
  // update this dialogue's entry in overview so tab reflects new progress
  if (lastOverviewStates && lastOverviewStates.length) {
    const idx = lastOverviewStates.findIndex((s) => s.dialogue_id === state.dialogue_id);
    if (idx !== -1) lastOverviewStates[idx] = state;
    else lastOverviewStates.push(state);
    renderTabs();
  }
}

function flattenSummaryFacts(node, path = []) {
  const facts = [];
  if (node === null || node === undefined) return facts;
  if (Array.isArray(node)) {
    node.forEach((item, idx) => facts.push(...flattenSummaryFacts(item, [...path, String(idx)])));
    return facts;
  }
  if (typeof node === "object") {
    Object.entries(node).forEach(([key, value]) => facts.push(...flattenSummaryFacts(value, [...path, key])));
    return facts;
  }
  const str = String(node).trim();
  if (!str) return facts;
  facts.push({ path: path.join("."), value: str });
  return facts;
}

function valueToText(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.map((v) => humanizeValue(v)).join(", ");
  if (typeof value === "object") return "";
  return humanizeValue(value);
}

function humanizeToken(text) {
  return String(text).replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
}

function humanizeValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return humanizeToken(value);
  return String(value);
}

function detectPersonGender(data) {
  const identity = data?.identity || {};
  const candidates = [];
  if (identity.gender) candidates.push(String(identity.gender));
  if (Array.isArray(identity.genders)) identity.genders.forEach((g) => candidates.push(String(g)));
  const txt = candidates.join(" ").toLowerCase();
  if (txt.includes("female")) return "female";
  if (txt.includes("male")) return "male";
  return "unknown";
}

function getCategoryConfig() {
  return [
    { key: "identity",     icon: "👤", label: t("catPersonal") },
    { key: "relationship", icon: "💞", label: t("catRelationship") },
    { key: "work_money",   icon: "💼", label: t("catWork") },
    { key: "lifestyle",    icon: "🏠", label: t("catLifestyle") },
    { key: "sexual",       icon: "🔥", label: t("catSexual") },
    { key: "personality",  icon: "🧠", label: t("catPersonality") },
  ];
}

const SKIP_KEYS = new Set(["gender", "genders"]);

function makeOperatorNote(key, value) {
  const lowered = String(key).toLowerCase();
  if (SKIP_KEYS.has(lowered)) return "";
  if (typeof value === "boolean") return value ? humanizeToken(key) : "";
  const text = valueToText(value);
  return text || "";
}

function renderProfileCard(title, data) {
  const sections = getCategoryConfig()
    .map((cat) => {
      const obj = data?.[cat.key];
      if (!obj || typeof obj !== "object") return "";
      const notes = [...new Set(
        Object.entries(obj).map(([k, v]) => makeOperatorNote(k, v)).filter(Boolean)
      )];
      if (!notes.length) return "";
      return `<div class="profile-section">
        <span class="profile-section-icon">${cat.icon}</span>
        <span class="profile-section-text">${notes.join(", ")}</span>
      </div>`;
    })
    .filter(Boolean)
    .join("");

  if (!sections) {
    return `<div class="profile-card profile-card--empty">
      <h3 class="profile-card-title">${title}</h3>
      <div class="hint">${t("noData")}</div>
    </div>`;
  }

  return `<div class="profile-card">
    <h3 class="profile-card-title">${title}</h3>
    <div class="profile-sections">${sections}</div>
  </div>`;
}

function renderSummaryFacts(summary) {
  if (!summaryFactsEl) return;
  const users = summary?.users || {};
  const userData = users.user || {};
  const personaData = users.persona || {};

  const genderA = detectPersonGender(userData);
  const genderB = detectPersonGender(personaData);
  const labelA = genderA === "female" ? t("labelFemale") : genderA === "male" ? t("labelMale") : t("labelUser");
  const labelB = genderB === "female" ? t("labelFemale") : genderB === "male" ? t("labelMale") : t("labelPersona");

  const facts = flattenSummaryFacts(summary);
  if (!facts.length) {
    summaryFactsEl.innerHTML = "";
    return;
  }

  summaryFactsEl.innerHTML = renderProfileCard(labelA, userData) + renderProfileCard(labelB, personaData);
}

function renderSummaryOverview(states) {
  lastOverviewStates = states || [];
  if (!summaryOverviewEl) return;
  if (!Array.isArray(states) || !states.length) {
    summaryOverviewEl.innerHTML = `<div class="overview-item">${t("noSummary")}</div>`;
    return;
  }
  summaryOverviewEl.innerHTML = states
    .map((s) => {
      const pct = s.total_messages ? Math.round((s.processed_messages / s.total_messages) * 100) : 0;
      const activeClass = s.dialogue_id === activeDialogueId ? "active" : "";
      return `<div class="overview-item ${activeClass}">
        <div><b>#${s.dialogue_id}</b> (${s.processed_messages}/${s.total_messages}, ${pct}%)</div>
        <div>${t("facts")}: ${s.fact_count || 0}</div>
      </div>`;
    })
    .join("");
}

async function loadSummaryOverview() {
  const states = await fetchJson("api/summaries");
  renderSummaryOverview(states);
  renderTabs();
}

async function loadSummary(dialogueId) {
  const state = await fetchJson(`api/dialogues/${dialogueId}/summary`);
  renderSummary(state);
}

async function selectDialogue(dialogueId) {
  activeDialogueId = dialogueId;
  renderTabs();
  setStatus(t("loading", dialogueId));

  const [messagesPayload] = await Promise.all([
    fetchJson(`api/dialogues/${dialogueId}/messages?lang=${currentLang}&limit=${MESSAGES_PREVIEW_LIMIT}`),
    loadSummary(dialogueId),
  ]);

  const isLegacyArray = Array.isArray(messagesPayload);
  const messages = isLegacyArray ? messagesPayload : messagesPayload.messages;
  const returnedMessages = isLegacyArray ? messagesPayload.length : messagesPayload.returned_messages;
  const totalMessages = isLegacyArray ? messagesPayload.length : messagesPayload.total_messages;
  // Show a note if the API fell back to sv (requested lang not available yet)
  const servedLang = isLegacyArray ? "sv" : (messagesPayload.lang || "sv");
  const showNote = !isLegacyArray && servedLang !== currentLang && currentLang !== "sv";

  renderMessages(messages, showNote);

  if (messagesMetaEl) {
    messagesMetaEl.textContent = returnedMessages < totalMessages
      ? t("shownFirst", returnedMessages, totalMessages)
      : t("shownAll", totalMessages);
  }
  await loadSummaryOverview();
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  if (!hasRequiredDom()) {
    console.error("Missing core DOM nodes for app initialization.");
    return;
  }

  // Load chunk size from server then apply i18n (so button shows correct number)
  try {
    const status = await fetchJson("api/status");
    if (status.chunk_size) chunkSize = status.chunk_size;
  } catch (_) {}

  applyI18n();

  try {
    dialogues = await fetchJson("api/dialogues");
    if (!dialogues.length) {
      setStatus(t("noDialogues"), true);
      return;
    }
    activeDialogueId = dialogues[0].dialogue_id;
    renderTabs();
    await selectDialogue(activeDialogueId);
    await loadSummaryOverview();
  } catch (error) {
    setStatus(t("loadError", error.message), true);
  }
}

// prompts are managed on prompts.php and stored in PHP session

// ─── Event handlers ───────────────────────────────────────────────────────────

document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.onclick = () => setLang(btn.dataset.lang);
});

if (btnSummaryNext) {
  btnSummaryNext.onclick = async () => {
    if (!activeDialogueId || isBusy) return;
    setBusy(true);
    setStatus(t("summaryUpdating"));
    try {
      const state = await fetchJson(`api/dialogues/${activeDialogueId}/summary/next`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lang: currentLang }),
      });
      renderSummary(state);
      await loadSummaryOverview();
    } catch (error) {
      setStatus(t("summaryError", error.message), true);
    } finally {
      setBusy(false);
    }
  };
}

if (btnSummaryFull) {
  btnSummaryFull.onclick = async () => {
    if (!activeDialogueId || isBusy) return;
    setBusy(true);
    try {
      let iterations = 0;
      while (iterations < 5000) {
        iterations++;
        setStatus(t("scanStep", iterations));
        const state = await fetchJson(`api/dialogues/${activeDialogueId}/summary/next`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lang: currentLang }),
        });
        renderSummary(state);
        await loadSummaryOverview();
        if (state.status === "already_complete" || state.is_complete) {
          setStatus(t("scanDone", state));
          break;
        }
      }
    } catch (error) {
      setStatus(t("scanError", error.message), true);
    } finally {
      setBusy(false);
    }
  };
}

if (btnSummaryReset) {
  btnSummaryReset.onclick = async () => {
    if (!activeDialogueId || isBusy) return;
    setBusy(true);
    setStatus(t("btnReset") + "…");
    try {
      const state = await fetchJson(`api/dialogues/${activeDialogueId}/summary/reset`, { method: "POST" });
      renderSummary(state);
      await loadSummaryOverview();
    } catch (error) {
      setStatus(t("resetError", error.message), true);
    } finally {
      setBusy(false);
    }
  };
}

init();
