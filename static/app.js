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
    element.style.color = "var(--ember)";
    element.style.borderColor = "rgba(255, 139, 61, 0.28)";
    element.style.background = "rgba(255, 139, 61, 0.1)";
    return;
  }
  if (tone === "success") {
    element.style.color = "var(--mint)";
    element.style.borderColor = "rgba(117, 242, 208, 0.28)";
    element.style.background = "rgba(117, 242, 208, 0.1)";
    return;
  }
  if (tone === "error") {
    element.style.color = "var(--danger)";
    element.style.borderColor = "rgba(255, 141, 141, 0.3)";
    element.style.background = "rgba(255, 141, 141, 0.1)";
    return;
  }
  element.style.color = "var(--steel)";
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
      headline: `Metin → ${method.label}`,
      description: method.encode_title,
      inputLabel: method.encode_input_label,
      outputLabel: method.encode_output_label,
      placeholder: method.encode_placeholder,
      example: method.encode_example,
      endpoint: currentMode === "single" ? "/encode" : "/bulk/encode",
      outputHint: `${method.label} formatında üretilecek sonuç burada görünür.`,
      detailLabel: "Metinden formata örnek",
      buttonLabel: "Formata dönüştür",
    };
  }

  return {
    headline: `${method.label} → Metin`,
    description: method.decode_title,
    inputLabel: method.decode_input_label,
    outputLabel: method.decode_output_label,
    placeholder: method.decode_placeholder,
    example: method.decode_example,
    endpoint: currentMode === "single" ? "/decode" : "/bulk/decode",
    outputHint: "Çözülmüş metin burada görünür.",
    detailLabel: "Formattan metne örnek",
    buttonLabel: "Metne çöz",
  };
}

function resetResultState() {
  copyBuffer = "";
  reusableBuffer = "";
  copyButton.disabled = true;
  reuseButton.disabled = true;
  resultOutput.textContent = "Henüz sonuç yok.";
  setResultBadge("Hazır", "idle");
}

function updateWorkflow() {
  const method = currentMethod();
  const meta = getDirectionMeta(method);
  const modeLabel = currentMode === "single" ? "tekil" : "toplu";
  const exampleValue = currentMode === "bulk" ? `${meta.example}\n${meta.example}` : meta.example;

  flowHeadline.textContent = meta.headline;
  flowDescription.textContent = `${meta.description} Bu seçim şu anda ${modeLabel} modda çalışacak.`;
  methodKeyBadge.textContent = method.key;
  methodCategoryBadge.textContent = method.category;
  endpointPreview.textContent = `POST ${meta.endpoint}`;
  inputTypePreview.textContent = meta.inputLabel;
  outputTypePreview.textContent = meta.outputLabel;
  inputPanelTitle.textContent = meta.inputLabel;
  outputPanelTitle.textContent = meta.outputLabel;
  inputPanelHint.textContent =
    currentMode === "single"
      ? `${meta.inputLabel} alanına tek bir kayıt girin.`
      : `${meta.inputLabel} alanına her satıra bir kayıt gelecek şekilde girin.`;
  outputPanelHint.textContent =
    currentMode === "single"
      ? meta.outputHint
      : "Toplu modda özet ve satır bazlı sonuçlar sağ panelde gösterilir.";
  singleInputLabel.textContent = meta.inputLabel;
  bulkInputLabel.textContent = `${meta.inputLabel} listesi`;
  singleInput.placeholder = meta.placeholder;
  bulkInput.placeholder = exampleValue;
  runButton.textContent = meta.buttonLabel;
  detailTitle.textContent = method.label;
  detailDescription.textContent = method.description;
  detailCategory.textContent = method.category;
  detailExampleLabel.textContent = meta.detailLabel;
  detailExampleValue.textContent = meta.example;
  resetResultState();
  setStatus(`${meta.headline} akışı hazır. İsterseniz örnek veri yükleyip hemen deneyin.`, "info");
}

function loadExample() {
  const meta = getDirectionMeta(currentMethod());
  if (currentMode === "single") {
    singleInput.value = meta.example;
  } else {
    bulkInput.value = `${meta.example}\n${meta.example}`;
  }
  setStatus("Seçili yön ve yönteme uygun örnek veri alana yerleştirildi.", "success");
}

function clearWorkspace() {
  singleInput.value = "";
  bulkInput.value = "";
  resetResultState();
  setStatus("Girdi ve sonuç alanları temizlendi.", "info");
}

function reuseResult() {
  if (!reusableBuffer) {
    setStatus("Yeniden kullanılabilir bir sonuç yok.", "error");
    return;
  }
  if (currentMode === "single") {
    singleInput.value = reusableBuffer;
  } else {
    bulkInput.value = reusableBuffer;
  }
  setStatus("Sonuç tekrar giriş alanına taşındı.", "success");
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
    option.textContent = "Eşleşen yöntem bulunamadı";
    methodSelect.append(option);
    methodSelect.disabled = true;
    setStatus("Arama sonucu eşleşen yöntem bulunamadı.", "error");
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
    setStatus("Önce geçerli bir yöntem seçin.", "error");
    return;
  }

  const meta = getDirectionMeta(method);
  const endpoint = meta.endpoint;
  let payload;

  if (currentMode === "single") {
    payload = { data: singleInput.value, method: method.key };
    if (!payload.data.trim()) {
      setStatus(`${meta.inputLabel} boş olamaz.`, "error");
      setResultBadge("validation", "error");
      return;
    }
  } else {
    const items = bulkInput.value
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    if (!items.length) {
      setStatus(`${meta.inputLabel} listesinde en az bir dolu satır olmalıdır.`, "error");
      setResultBadge("validation", "error");
      return;
    }
    payload = { items, method: method.key };
  }

  setResultBadge("loading", "loading");
  resultOutput.textContent = "İşleniyor...";
  copyButton.disabled = true;
  reuseButton.disabled = true;
  copyBuffer = "";
  reusableBuffer = "";
  setStatus(`${meta.headline} isteği gönderildi.`, "info");

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();

    if (!response.ok) {
      resultOutput.textContent = result.message || "Beklenmeyen bir hata oluştu.";
      setResultBadge(result.status || "error", "error");
      setStatus(result.message || "İşlem başarısız oldu.", "error");
      return;
    }

    if (currentMode === "single") {
      const output = result.result || "";
      resultOutput.textContent = output;
      copyBuffer = result.clipboard_ready ? output : "";
      reusableBuffer = output;
      copyButton.disabled = !copyBuffer;
      reuseButton.disabled = !reusableBuffer;
      setResultBadge(result.status, "success");
      setStatus(`${meta.headline} işlemi tamamlandı.`, "success");
      return;
    }

    const lines = [
      `${meta.headline} | toplam ${result.summary.total}`,
      `Başarılı: ${result.summary.success_count}`,
      `Hatalı: ${result.summary.error_count}`,
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
    setResultBadge(result.status, result.status === "error" ? "error" : "success");
    setStatus(
      `Toplu işlem tamamlandı: ${result.summary.success_count}/${result.summary.total} başarılı.`,
      result.status === "error" ? "error" : "success",
    );
  } catch {
    resultOutput.textContent = "Ağ veya istemci tarafı bir hata oluştu.";
    setResultBadge("network", "error");
    setStatus("Sunucuya erişilemedi veya yanıt çözümlenemedi.", "error");
  }
}

async function copyResult() {
  if (!copyBuffer) {
    setStatus("Kopyalanabilir bir sonuç yok.", "error");
    return;
  }
  try {
    await navigator.clipboard.writeText(copyBuffer);
    setStatus("Sonuç panoya kopyalandı.", "success");
  } catch {
    setStatus("Tarayıcı panoya yazma izni vermedi.", "error");
  }
}

async function runSelfCheck() {
  selfCheckButton.disabled = true;
  healthOutput.textContent = "Self-check çalışıyor...";
  healthStatusBadge.textContent = "çalışıyor";
  applyBadgeTone(healthStatusBadge, "loading");

  try {
    const response = await fetch("/health/transformations");
    const payload = await response.json();
    const tone = payload.status === "ok" ? "success" : "error";

    healthStatusBadge.textContent = payload.status;
    applyBadgeTone(healthStatusBadge, tone);
    healthCheckedCount.textContent = String(payload.checked_methods || 0);
    healthSuccessCount.textContent = String(payload.success_count || 0);
    healthErrorCount.textContent = String(payload.error_count || 0);

    const lines = [
      `Durum: ${payload.status}`,
      `Kontrol edilen: ${payload.checked_methods}`,
      `Başarılı: ${payload.success_count}`,
      `Hatalı: ${payload.error_count}`,
      "",
      ...(payload.results || []).map((item) => {
        const detail = item.message || "";
        return `${item.method} [${item.status}] ${detail}`;
      }),
    ];
    healthOutput.textContent = lines.join("\n");
  } catch {
    healthStatusBadge.textContent = "hata";
    applyBadgeTone(healthStatusBadge, "error");
    healthOutput.textContent = "Self-check endpoint'ine ulaşılamadı.";
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

refreshMethodOptions("");
setDirection("encode");
setMode("single");
