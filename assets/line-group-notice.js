const STORAGE_KEY = "tool.line_group_notice.form.v1";
const CHATGPT_URL = "https://chatgpt.com/";

const form = document.getElementById("line-notice-form");
const noticeType = document.getElementById("noticeType");
const subject = document.getElementById("subject");
const keyPoints = document.getElementById("keyPoints");
const audience = document.getElementById("audience");
const deadline = document.getElementById("deadline");
const assignments = document.getElementById("assignments");
const replyRule = document.getElementById("replyRule");
const extraNotes = document.getElementById("extraNotes");
const promptPreview = document.getElementById("promptPreview");
const runFlowBtn = document.getElementById("runFlowBtn");
const copyBtn = document.getElementById("copyBtn");
const clearSavedBtn = document.getElementById("clearSavedBtn");
const statusEl = document.getElementById("status");
const savedInfoEl = document.getElementById("savedInfo");

function textToBullets(text, emptyFallback) {
  const bullets = text
    .split("\n")
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => `- ${v}`)
    .join("\n");
  return bullets || `- ${emptyFallback}`;
}

function readForm() {
  return {
    noticeType: noticeType.value.trim(),
    subject: subject.value.trim(),
    keyPoints: keyPoints.value.trim(),
    audience: audience.value.trim(),
    deadline: deadline.value.trim(),
    assignments: assignments.value.trim(),
    replyRule: replyRule.value.trim(),
    extraNotes: extraNotes.value.trim(),
  };
}

function writeForm(data) {
  noticeType.value = data.noticeType || "";
  subject.value = data.subject || "";
  keyPoints.value = data.keyPoints || "";
  audience.value = data.audience || "";
  deadline.value = data.deadline || "";
  assignments.value = data.assignments || "";
  replyRule.value = data.replyRule || "";
  extraNotes.value = data.extraNotes || "";
}

function buildPrompt(data) {
  const keyPointsBullets = textToBullets(data.keyPoints, "（未填）");
  const assignmentBullets = textToBullets(data.assignments, "（無）");
  const audienceText = data.audience || "全體老師";
  const customReply = data.replyRule
    ? data.replyRule
    : "如確認清楚沒有任何問題，請回覆此訊息表情。如有問題可私下聯絡我。";

  return [
    "請你扮演校務與班務溝通助理，幫我產生可直接貼到 LINE 老師群組的公告訊息。",
    "",
    "【任務】",
    "請根據輸入資料，產生 3 個版本：",
    "1) 完整版（資訊完整、正式）",
    "2) 精簡版（快速閱讀）",
    "3) 提醒版（行動重點導向）",
    "",
    "【必須遵守】",
    "- 語氣務實、清楚、可執行，不要 AI 腔與空話。",
    "- 每個版本都要可直接複製貼到 LINE。",
    "- 可用 emoji，但整則最多 3 個（避免過多）。",
    "- 不要輸出任何說明文字，只輸出三個版本內容。",
    "",
    "【輸入資料】",
    `- 公告類型：${data.noticeType || "（未填）"}`,
    `- 主旨：${data.subject || "（未填）"}`,
    "- 重點事項：",
    keyPointsBullets,
    `- 對象（選填）：${audienceText}`,
    `- 截止時間（選填）：${data.deadline || "（無）"}`,
    "- 分工（選填）：",
    assignmentBullets,
    `- 回覆要求（選填）：${customReply}`,
    `- 備註（選填）：${data.extraNotes || "（無）"}`,
    "",
    "【輸出格式（每一版都要完全照這個格式）】",
    "內文：",
    "【主旨】",
    "對象：xxxx",
    "xxxxxxxx請協助配合",
    "1. ",
    "2. ",
    "3. ",
    "4. ",
    "回覆：如確認清楚沒有任何問題，請回覆此訊息表情。如有問題可私下聯絡我。",
    "",
    "【1) 完整版】",
    "（依格式輸出）",
    "",
    "【2) 精簡版】",
    "（依格式輸出）",
    "",
    "【3) 提醒版】",
    "（依格式輸出）",
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

function validateRequired(data) {
  if (!data.noticeType || !data.subject || !data.keyPoints) {
    setStatus("請先填完必填欄位：公告類型、主旨、重點事項");
    return false;
  }
  return true;
}

async function copyPrompt() {
  const data = readForm();
  if (!validateRequired(data)) {
    return false;
  }

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

