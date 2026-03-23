const methods = JSON.parse(document.getElementById("methods-data").textContent);
const methodMap = Object.fromEntries(methods.map((method) => [method.key, method]));

const encodeFlowButton = document.getElementById("encodeFlowButton");
const decodeFlowButton = document.getElementById("decodeFlowButton");
const singleModeButton = document.getElementById("singleModeButton");
const bulkModeButton = document.getElementById("bulkModeButton");
const methodSearch = document.getElementById("methodSearch");
const methodSelect = document.getElementById("methodSelect");
const flowHeadline = document.getElementById("flowHeadline");
const flowDescription = document.getElementById("flowDescription");
const methodKeyBadge = document.getElementById("methodKeyBadge");
const methodCategoryBadge = document.getElementById("methodCategoryBadge");
const endpointPreview = document.getElementById("endpointPreview");
const inputTypePreview = document.getElementById("inputTypePreview");
const outputTypePreview = document.getElementById("outputTypePreview");
const inputPanelTitle = document.getElementById("inputPanelTitle");
const outputPanelTitle = document.getElementById("outputPanelTitle");
const inputPanelHint = document.getElementById("inputPanelHint");
const outputPanelHint = document.getElementById("outputPanelHint");
const singleInputWrap = document.getElementById("singleInputWrap");
const bulkInputWrap = document.getElementById("bulkInputWrap");
const singleInputLabel = document.getElementById("singleInputLabel");
const bulkInputLabel = document.getElementById("bulkInputLabel");
const singleInput = document.getElementById("singleInput");
const bulkInput = document.getElementById("bulkInput");
const runButton = document.getElementById("runButton");
const loadExampleButton = document.getElementById("loadExampleButton");
const clearButton = document.getElementById("clearButton");
const reuseButton = document.getElementById("reuseButton");
const copyButton = document.getElementById("copyButton");
const statusMessage = document.getElementById("statusMessage");
const resultOutput = document.getElementById("resultOutput");
const resultBadge = document.getElementById("resultBadge");
const detailTitle = document.getElementById("detailTitle");
const detailDescription = document.getElementById("detailDescription");
const detailCategory = document.getElementById("detailCategory");
const detailExampleLabel = document.getElementById("detailExampleLabel");
const detailExampleValue = document.getElementById("detailExampleValue");
const selfCheckButton = document.getElementById("selfCheckButton");
const healthStatusBadge = document.getElementById("healthStatusBadge");
const healthCheckedCount = document.getElementById("healthCheckedCount");
const healthSuccessCount = document.getElementById("healthSuccessCount");
const healthErrorCount = document.getElementById("healthErrorCount");
const healthOutput = document.getElementById("healthOutput");

let currentDirection = "encode";
let currentMode = "single";
let copyBuffer = "";
let reusableBuffer = "";

function currentMethod() {
  return methodMap[methodSelect.value];
}

function setStatus(message, tone = "info") {
  statusMessage.className = "status-box";
  if (tone === "success") {
    statusMessage.classList.add("is-success");
  } else if (tone === "error") {
    statusMessage.classList.add("is-error");
  }
  statusMessage.textContent = message;
}

function setResultBadge(label, tone = "idle") {
  resultBadge.className = "result-badge";
  if (tone === "loading") {
    applyBadgeTone(resultBadge, "loading");
  } else if (tone === "success") {
    applyBadgeTone(resultBadge, "success");
  } else if (tone === "error") {
    applyBadgeTone(resultBadge, "error");
  } else {
    applyBadgeTone(resultBadge, "idle");
  }
  resultBadge.textContent = label;
}

function applyBadgeTone(element, tone) {
  if (tone === "loading") {
    element.style.color = "var(--warning)";
    element.style.borderColor = "rgba(255, 184, 107, 0.3)";
    element.style.background = "rgba(255, 184, 107, 0.12)";
    return;
  }
  if (tone === "success") {
    element.style.color = "var(--accent)";
    element.style.borderColor = "rgba(76, 214, 176, 0.28)";
    element.style.background = "rgba(76, 214, 176, 0.12)";
    return;
  }
  if (tone === "error") {
    element.style.color = "var(--danger)";
    element.style.borderColor = "rgba(255, 140, 140, 0.3)";
    element.style.background = "rgba(255, 140, 140, 0.12)";
    return;
  }
  element.style.color = "var(--text-muted)";
  element.style.borderColor = "var(--line)";
  element.style.background = "transparent";
}

function setDirection(direction) {
  currentDirection = direction;
  encodeFlowButton.classList.toggle("is-active", direction === "encode");
  decodeFlowButton.classList.toggle("is-active", direction === "decode");
  updateWorkflow();
}

function setMode(mode) {
  currentMode = mode;
  singleModeButton.classList.toggle("is-active", mode === "single");
  bulkModeButton.classList.toggle("is-active", mode === "bulk");
  singleInputWrap.classList.toggle("is-hidden", mode !== "single");
  bulkInputWrap.classList.toggle("is-hidden", mode !== "bulk");
  updateWorkflow();
}

function getDirectionMeta(method) {
  if (currentDirection === "encode") {
    return {
      headline: `Text → ${method.label}`,
      description: method.description,
      inputLabel: method.encode_input_label,
      outputLabel: method.encode_output_label,
      placeholder: method.encode_placeholder,
      example: method.encode_example,
      endpoint: currentMode === "single" ? "/encode" : "/bulk/encode",
      outputHint: `${method.label} output appears in this panel.`,
      detailLabel: "Text to format sample",
      buttonLabel: "Run Transform",
    };
  }

  return {
    headline: `${method.label} → Text`,
    description: method.description,
    inputLabel: method.decode_input_label,
    outputLabel: method.decode_output_label,
    placeholder: method.decode_placeholder,
    example: method.decode_example,
    endpoint: currentMode === "single" ? "/decode" : "/bulk/decode",
    outputHint: "Decoded plain text appears in this panel.",
    detailLabel: "Format to text sample",
    buttonLabel: "Decode to Text",
  };
}

function resetResultState() {
  copyBuffer = "";
  reusableBuffer = "";
  copyButton.disabled = true;
  reuseButton.disabled = true;
  resultOutput.textContent = "No result yet.";
  setResultBadge("Ready", "idle");
}

function updateWorkflow() {
  const method = currentMethod();
  const meta = getDirectionMeta(method);
  const modeLabel = currentMode === "single" ? "single" : "batch";
  const exampleValue = currentMode === "bulk" ? `${meta.example}\n${meta.example}` : meta.example;

  flowHeadline.textContent = meta.headline;
  flowDescription.textContent = `${meta.description} Active mode: ${modeLabel}.`;
  methodKeyBadge.textContent = method.key;
  methodCategoryBadge.textContent = method.category;
  endpointPreview.textContent = `POST ${meta.endpoint}`;
  inputTypePreview.textContent = meta.inputLabel;
  outputTypePreview.textContent = meta.outputLabel;
  inputPanelTitle.textContent = meta.inputLabel;
  outputPanelTitle.textContent = meta.outputLabel;
  inputPanelHint.textContent =
    currentMode === "single"
      ? `Enter a single record in the ${meta.inputLabel.toLowerCase()} field.`
      : `Enter one record per line in the ${meta.inputLabel.toLowerCase()} field.`;
  outputPanelHint.textContent =
    currentMode === "single"
      ? meta.outputHint
      : "Batch mode returns a summary plus line-by-line output in the result panel.";
  singleInputLabel.textContent = meta.inputLabel;
  bulkInputLabel.textContent = `${meta.inputLabel} list`;
  singleInput.placeholder = meta.placeholder;
  bulkInput.placeholder = exampleValue;
  runButton.textContent = meta.buttonLabel;
  detailTitle.textContent = method.label;
  detailDescription.textContent = method.description;
  detailCategory.textContent = method.category;
  detailExampleLabel.textContent = meta.detailLabel;
  detailExampleValue.textContent = meta.example;
  resetResultState();
  setStatus(`${meta.headline} is ready. Load a sample or start working with your own input.`, "info");
}

function loadExample() {
  const meta = getDirectionMeta(currentMethod());
  if (currentMode === "single") {
    singleInput.value = meta.example;
  } else {
    bulkInput.value = `${meta.example}\n${meta.example}`;
  }
  setStatus("A sample payload for the current method has been loaded.", "success");
}

function clearWorkspace() {
  singleInput.value = "";
  bulkInput.value = "";
  resetResultState();
  setStatus("Source and result areas were cleared.", "info");
}

function reuseResult() {
  if (!reusableBuffer) {
    setStatus("There is no reusable result yet.", "error");
    return;
  }
  if (currentMode === "single") {
    singleInput.value = reusableBuffer;
  } else {
    bulkInput.value = reusableBuffer;
  }
  setStatus("The latest output was copied back into the input area.", "success");
}

function refreshMethodOptions(searchTerm) {
  const normalizedSearch = searchTerm.trim().toLowerCase();
  const currentValue = methodSelect.value;
  const filteredMethods = methods.filter((method) => {
    if (!normalizedSearch) {
      return true;
    }
    const haystack = [
      method.key,
      method.label,
      method.category,
      method.description,
    ].join(" ").toLowerCase();
    return haystack.includes(normalizedSearch);
  });

  methodSelect.innerHTML = "";
  for (const method of filteredMethods) {
    const option = document.createElement("option");
    option.value = method.key;
    option.textContent = method.label;
    methodSelect.append(option);
  }

  if (!filteredMethods.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No matching method";
    methodSelect.append(option);
    methodSelect.disabled = true;
    setStatus("No method matched the current search term.", "error");
    resetResultState();
    return;
  }

  methodSelect.disabled = false;
  const nextValue = filteredMethods.some((method) => method.key === currentValue)
    ? currentValue
    : filteredMethods[0].key;
  methodSelect.value = nextValue;
  updateWorkflow();
}

async function performTransform() {
  const method = currentMethod();
  if (!method) {
    setStatus("Select a valid method before running a transformation.", "error");
    return;
  }

  const meta = getDirectionMeta(method);
  const endpoint = meta.endpoint;
  let payload;

  if (currentMode === "single") {
    payload = { data: singleInput.value, method: method.key };
    if (!payload.data.trim()) {
      setStatus(`${meta.inputLabel} cannot be empty.`, "error");
      setResultBadge("Invalid", "error");
      return;
    }
  } else {
    const items = bulkInput.value
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    if (!items.length) {
      setStatus(`Batch input requires at least one non-empty line.`, "error");
      setResultBadge("Invalid", "error");
      return;
    }
    payload = { items, method: method.key };
  }

  setResultBadge("Running", "loading");
  resultOutput.textContent = "Processing...";
  copyButton.disabled = true;
  reuseButton.disabled = true;
  copyBuffer = "";
  reusableBuffer = "";
  setStatus(`${meta.headline} request has been sent.`, "info");

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
      resultOutput.textContent = result.message || "An unexpected server error occurred.";
      setResultBadge("Error", "error");
      setStatus(result.message || "The transformation failed.", "error");
      return;
    }

    if (currentMode === "single") {
      const output = result.result || "";
      resultOutput.textContent = output;
      copyBuffer = result.clipboard_ready ? output : "";
      reusableBuffer = output;
      copyButton.disabled = !copyBuffer;
      reuseButton.disabled = !reusableBuffer;
      setResultBadge("Done", "success");
      setStatus(`${meta.headline} completed successfully.`, "success");
      return;
    }

    const lines = [
      `${meta.headline} | total ${result.summary.total}`,
      `Succeeded: ${result.summary.success_count}`,
      `Failed: ${result.summary.error_count}`,
      "",
      ...result.results.map((item) => {
        const content = item.status === "success" ? item.result : item.message;
        return `${item.index + 1}. [${item.status}] ${content}`;
      }),
    ];
    resultOutput.textContent = lines.join("\n");
    copyBuffer = result.combined_result || "";
    reusableBuffer = result.combined_result || "";
    copyButton.disabled = !result.clipboard_ready;
    reuseButton.disabled = !reusableBuffer;
    setResultBadge(result.status === "partial_success" ? "Partial" : "Done", result.status === "error" ? "error" : "success");
    setStatus(
      `Batch run completed: ${result.summary.success_count}/${result.summary.total} succeeded.`,
      result.status === "error" ? "error" : "success",
    );
  } catch {
    resultOutput.textContent = "A network or client-side error interrupted the request.";
    setResultBadge("Offline", "error");
    setStatus("The server could not be reached or the response could not be parsed.", "error");
  }
}

async function copyResult() {
  if (!copyBuffer) {
    setStatus("There is no copyable result yet.", "error");
    return;
  }
  try {
    await navigator.clipboard.writeText(copyBuffer);
    setStatus("The result has been copied to the clipboard.", "success");
  } catch {
    setStatus("The browser denied clipboard access.", "error");
  }
}

async function runSelfCheck() {
  selfCheckButton.disabled = true;
  healthOutput.textContent = "System check is running...";
  healthStatusBadge.textContent = "Running";
  applyBadgeTone(healthStatusBadge, "loading");

  try {
    const response = await fetch("/health/transformations");
    const payload = await response.json();
    const tone = payload.status === "ok" ? "success" : "error";

    healthStatusBadge.textContent = payload.status === "ok" ? "Healthy" : "Issue";
    applyBadgeTone(healthStatusBadge, tone);
    healthCheckedCount.textContent = String(payload.checked_methods || 0);
    healthSuccessCount.textContent = String(payload.success_count || 0);
    healthErrorCount.textContent = String(payload.error_count || 0);

    const lines = [
      `Status: ${payload.status}`,
      `Checked: ${payload.checked_methods}`,
      `Passed: ${payload.success_count}`,
      `Failed: ${payload.error_count}`,
      "",
      ...(payload.results || []).map((item) => {
        const detail = item.message || "";
        return `${item.method} [${item.status}] ${detail}`;
      }),
    ];
    healthOutput.textContent = lines.join("\n");
  } catch {
    healthStatusBadge.textContent = "Error";
    applyBadgeTone(healthStatusBadge, "error");
    healthOutput.textContent = "The system check endpoint could not be reached.";
  } finally {
    selfCheckButton.disabled = false;
  }
}

encodeFlowButton.addEventListener("click", () => setDirection("encode"));
decodeFlowButton.addEventListener("click", () => setDirection("decode"));
singleModeButton.addEventListener("click", () => setMode("single"));
bulkModeButton.addEventListener("click", () => setMode("bulk"));
methodSelect.addEventListener("change", updateWorkflow);
methodSearch.addEventListener("input", (event) => refreshMethodOptions(event.target.value));
loadExampleButton.addEventListener("click", loadExample);
clearButton.addEventListener("click", clearWorkspace);
reuseButton.addEventListener("click", reuseResult);
runButton.addEventListener("click", performTransform);
copyButton.addEventListener("click", copyResult);
selfCheckButton.addEventListener("click", runSelfCheck);

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    performTransform();
  }
});

refreshMethodOptions("");
setDirection("encode");
setMode("single");
