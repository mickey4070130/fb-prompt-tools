const STORAGE_KEY = "tool.fb_post.form.v1";
const CHATGPT_URL = "https://chatgpt.com/";

const form = document.getElementById("fb-post-form");
const activityName = document.getElementById("activityName");
const grade = document.getElementById("grade");
const highlights = document.getElementById("highlights");
const childPerformance = document.getElementById("childPerformance");
const otherNotes = document.getElementById("otherNotes");
const promptPreview = document.getElementById("promptPreview");
const runFlowBtn = document.getElementById("runFlowBtn");
const copyBtn = document.getElementById("copyBtn");
const clearSavedBtn = document.getElementById("clearSavedBtn");
const statusEl = document.getElementById("status");
const savedInfoEl = document.getElementById("savedInfo");

function textToBullets(text) {
  return text
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => `- ${v}`)
    .join("\n");
}

function readForm() {
  return {
    activityName: activityName.value.trim(),
    grade: grade.value.trim(),
    highlights: highlights.value.trim(),
    childPerformance: childPerformance.value.trim(),
    otherNotes: otherNotes.value.trim(),
  };
}

function writeForm(data) {
  activityName.value = data.activityName || "";
  grade.value = data.grade || "";
  highlights.value = data.highlights || "";
  childPerformance.value = data.childPerformance || "";
  otherNotes.value = data.otherNotes || "";
}

function buildPrompt(data) {
  const highlightsBullets = textToBullets(data.highlights);
  const performanceBullets = textToBullets(data.childPerformance);
  const otherText = data.otherNotes ? data.otherNotes : "（無）";

  return [
    "請你扮演資深班主任文案助手，根據以下資料產生 Facebook 貼文。",
    "",
    "請一次產出三種風格版本：",
    "1. 專業風",
    "2. 溫馨風",
    "3. 痛點風（先點出家長常見擔心，再給具體做法，不製造焦慮）",
    "",
    "重要限制：",
    "- 內容中禁止出現「安親」「課輔」兩詞。",
    "- 若需提及班別，請使用「全科班」或「美語班」。",
    "- 語氣自然，不要有 AI 感，不要使用空泛口號。",
    "",
    "長度與符號規則：",
    "- 每篇內文目標 80~120 字，上限 150 字。",
    "- 每篇 Hashtags 數量 3~6 個。",
    "- 可使用 emoji。",
    "- 標題可有 emoji，內文可有 emoji。",
    "- 每一段最多 1 個 emoji，整篇請控制在 3 個以內。",
    "",
    "內容真實性規則：",
    "- 文案必須可對應活動現場與照片，不得虛構。",
    "",
    "活動資料：",
    `- 活動名稱：${data.activityName || "（未填）"}`,
    `- 年級：${data.grade || "（未填）"}`,
    "- 亮點：",
    highlightsBullets || "- （未填）",
    "- 孩子表現：",
    performanceBullets || "- （未填）",
    `- 其他補充：${otherText}`,
    "",
    "輸出格式（請完全遵守）：",
    "- 每個風格都要：第一行是標題，第二行開始是內文，最後一行是 Hashtags。",
    "- 不要輸出「標題：」或「內文：」這種欄位標籤。",
    "",
    "【專業風】",
    "（第一行標題）",
    "（第二行開始內文）",
    "Hashtags：#... #... #...",
    "",
    "【溫馨風】",
    "（第一行標題）",
    "（第二行開始內文）",
    "Hashtags：#... #... #...",
    "",
    "【痛點風】",
    "（第一行標題）",
    "（第二行開始內文）",
    "Hashtags：#... #... #...",
  ].join("\n");
}

function setStatus(message) {
  statusEl.textContent = message;
}

function saveForm(data) {
  const payload = {
    ...data,
    savedAt: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  renderSavedInfo(payload.savedAt);
}

function renderSavedInfo(isoTime) {
  if (!isoTime) {
    savedInfoEl.textContent = "目前沒有儲存資料";
    return;
  }
  const date = new Date(isoTime);
  const text = Number.isNaN(date.getTime())
    ? isoTime
    : date.toLocaleString("zh-TW", { hour12: false });
  savedInfoEl.textContent = `上次儲存：${text}`;
}

function refreshPromptAndSave() {
  const data = readForm();
  promptPreview.value = buildPrompt(data);
  saveForm(data);
}

async function copyPrompt() {
  const text = promptPreview.value.trim();
  if (!text) {
    setStatus("沒有可複製內容");
    return false;
  }

  try {
    await navigator.clipboard.writeText(text);
    setStatus("已複製 Prompt");
    return true;
  } catch (_) {
    promptPreview.focus();
    promptPreview.select();
    const success = document.execCommand("copy");
    if (success) {
      setStatus("已複製 Prompt");
      return true;
    }
    setStatus("複製失敗，請手動全選複製");
    return false;
  }
}

async function runFullFlow() {
  const ok = await copyPrompt();
  if (ok) {
    window.location.href = CHATGPT_URL;
  }
}

function clearSavedData() {
  localStorage.removeItem(STORAGE_KEY);
  form.reset();
  promptPreview.value = buildPrompt(readForm());
  renderSavedInfo("");
  setStatus("已清除上次資料");
}

function init() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      const data = JSON.parse(raw);
      writeForm(data);
      renderSavedInfo(data.savedAt || "");
    } catch (_) {
      localStorage.removeItem(STORAGE_KEY);
      renderSavedInfo("");
    }
  } else {
    renderSavedInfo("");
  }

  promptPreview.value = buildPrompt(readForm());

  form.addEventListener("input", refreshPromptAndSave);
  copyBtn.addEventListener("click", copyPrompt);
  runFlowBtn.addEventListener("click", runFullFlow);
  clearSavedBtn.addEventListener("click", clearSavedData);
}

init();

