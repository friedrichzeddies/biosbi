const blogContent = document.getElementById("blog-content");
const paramsEditor = document.getElementById("params-editor");
const reloadParamsButton = document.getElementById("reload-params");
const saveParamsButton = document.getElementById("save-params");
const targetUrlInput = document.getElementById("target-url");
const messageInput = document.getElementById("message-input");
const payloadPreview = document.getElementById("payload-preview");
const relayOutput = document.getElementById("relay-output");
const sendJsonButton = document.getElementById("send-json");
const renderMessageButton = document.getElementById("render-message");
const statusText = document.getElementById("status");

function setStatus(message, tone = "") {
  statusText.textContent = message;
  statusText.className = tone;
}

function messagePayload() {
  return { message: messageInput.value };
}

function refreshPayloadPreview() {
  payloadPreview.textContent = JSON.stringify(messagePayload(), null, 2);
}

async function loadBlogContent() {
  try {
    const response = await fetch("/api/content");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not load blog markdown.");
    }
    blogContent.innerHTML = data.html;
  } catch (error) {
    blogContent.textContent = error.message;
    setStatus(error.message, "error");
  }
}

async function loadParameters() {
  reloadParamsButton.disabled = true;
  setStatus("Loading simulation parameters...");
  try {
    const response = await fetch("/api/simulation-parameters");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not load simulation parameters.");
    }
    paramsEditor.value = JSON.stringify(data.parameters, null, 2);
    setStatus("Loaded simulation parameters.", "ok");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    reloadParamsButton.disabled = false;
  }
}

async function saveParameters() {
  saveParamsButton.disabled = true;
  setStatus("Saving simulation parameters...");
  try {
    const parsed = JSON.parse(paramsEditor.value);
    const response = await fetch("/api/simulation-parameters", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parameters: parsed })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Could not save simulation parameters.");
    }
    paramsEditor.value = JSON.stringify(data.parameters, null, 2);
    setStatus("Saved simulation parameters.", "ok");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    saveParamsButton.disabled = false;
  }
}

async function renderMessageMarkdown() {
  renderMessageButton.disabled = true;
  setStatus("Rendering message markdown...");
  try {
    const response = await fetch("/api/render-markdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: messageInput.value })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Markdown rendering failed.");
    }
    relayOutput.textContent = data.html;
    setStatus("Rendered message markdown.", "ok");
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    renderMessageButton.disabled = false;
  }
}

async function sendJson() {
  sendJsonButton.disabled = true;
  setStatus("Sending JSON to local target...");
  try {
    const response = await fetch("/api/relay", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_url: targetUrlInput.value,
        payload: messagePayload()
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Relay request failed.");
    }
    relayOutput.textContent = JSON.stringify(data, null, 2);
    setStatus(`Relay succeeded with status ${data.status_code}.`, "ok");
  } catch (error) {
    relayOutput.textContent = error.message;
    setStatus(error.message, "error");
  } finally {
    sendJsonButton.disabled = false;
  }
}

messageInput.addEventListener("input", refreshPayloadPreview);
reloadParamsButton.addEventListener("click", loadParameters);
saveParamsButton.addEventListener("click", saveParameters);
renderMessageButton.addEventListener("click", renderMessageMarkdown);
sendJsonButton.addEventListener("click", sendJson);

refreshPayloadPreview();
loadBlogContent();
loadParameters();
