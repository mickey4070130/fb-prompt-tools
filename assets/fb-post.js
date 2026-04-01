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
    "請你扮演安親班資深班主任文案助手，根據以下資料產生 FB 貼文。",
    "",
    "請一次產出三種風格版本：",
    "1. 專業風",
    "2. 溫馨風",
    "3. 痛點風（先點出家長常見擔心，再給具體做法，不製造焦慮）",
    "",
    "請使用繁體中文，語氣自然，不要有 AI 感。",
    "避免空泛句型，例如「在這個充滿挑戰的時代」「讓我們一起」「每一位孩子都是獨一無二」。",
    "",
    "每一種風格都要符合：",
    "- 正文字數約 80~180 字（最多 250 字）",
    "- Hashtag 3~6 個",
    "- 內容要能對得上活動現場照片，不可虛構",
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
    "請用以下格式輸出：",
    "【專業風】",
    "標題：...",
    "內文：...",
    "Hashtags：#... #... #...",
    "",
    "【溫馨風】",
    "標題：...",
    "內文：...",
    "Hashtags：#... #... #...",
    "",
    "【痛點風】",
    "標題：...",
    "內文：...",
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
