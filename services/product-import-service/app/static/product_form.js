const form = document.querySelector("#product-form");
const imageRows = document.querySelector("#image-rows");
const specRows = document.querySelector("#spec-rows");
const imageTemplate = document.querySelector("#image-row-template");
const specTemplate = document.querySelector("#spec-row-template");
const statusPill = document.querySelector("#status-pill");
const messagePanel = document.querySelector("#message-panel");
const xmlPreview = document.querySelector("#xml-preview");
const downloadButton = document.querySelector("#download-button");

let latestXml = "";

document.querySelector("#scrape-button").addEventListener("click", scrapeProduct);
document.querySelector("#refresh-categories-button").addEventListener("click", refreshCategories);
document.querySelector("#preview-button").addEventListener("click", previewProduct);
document.querySelector("#upload-button").addEventListener("click", uploadProduct);
document.querySelector("#download-button").addEventListener("click", downloadXml);
document.querySelector("#add-image").addEventListener("click", () => addImageRow({}));
document.querySelector("#add-spec").addEventListener("click", () => addSpecRow({}));

addSpecRow({});

async function refreshCategories() {
  setBusy("Fetching categories");
  try {
    const data = await postJson("/api/categories/refresh", {});
    replaceCategoryOptions(data.categories || []);
    setMessage(`${data.message}\n${data.category_count} categories are available.`);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    setIdle();
  }
}

function replaceCategoryOptions(categories) {
  const select = document.querySelector("#category-id");
  const previousValue = select.value;
  const placeholder = new Option("Choose a category", "", true, false);
  placeholder.disabled = true;
  select.replaceChildren(placeholder);

  for (const category of categories) {
    select.add(new Option(category.label, category.id));
  }

  if (categories.some((category) => category.id === previousValue)) {
    select.value = previousValue;
  }
}

async function scrapeProduct() {
  const url = document.querySelector("#supplier-url").value.trim();
  if (!url) return setMessage("Supplier URL is required", true);

  setBusy("Scraping");
  try {
    const data = await postJson("/api/scrape", { url });
    document.querySelector("#product-name").value = data.product_name || "";
    document.querySelector("#product-number").value = data.product_number || "";
    document.querySelector("#hmi-number").value = data.hmi_number || "";
    document.querySelector("#title-tag").value = data.product_name || "";

    imageRows.innerHTML = "";
    for (const image of data.images || []) addImageRow(image);
    setMessage(`Scraped ${data.images.length} image(s).`);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    setIdle();
  }
}

async function previewProduct() {
  await generateProduct("/api/preview", "Preview ready");
}

async function uploadProduct() {
  await generateProduct("/api/upload", "Upload flow complete");
}

async function generateProduct(endpoint, successText) {
  setBusy("Generating");
  try {
    const data = await postJson(endpoint, collectDraft());
    latestXml = data.xml;
    xmlPreview.value = latestXml;
    downloadButton.disabled = false;
    setMessage(`${successText}\n\n${JSON.stringify(data.upload || data.media, null, 2)}`);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    setIdle();
  }
}

function collectDraft() {
  ensurePrimaryImage();
  return {
    source_url: document.querySelector("#supplier-url").value,
    product_name: document.querySelector("#product-name").value,
    product_number: document.querySelector("#product-number").value,
    hmi_number: document.querySelector("#hmi-number").value,
    price: document.querySelector("#price").value,
    category_id: document.querySelector("#category-id").value,
    title_tag: document.querySelector("#title-tag").value,
    meta_description: document.querySelector("#meta-description").value,
    meta_keywords: document.querySelector("#meta-keywords").value,
    short_description: document.querySelector("#short-description").value,
    long_description: document.querySelector("#long-description").value,
    images: [...document.querySelectorAll(".image-row")].map((row) => ({
      enabled: row.querySelector(".image-enabled").checked,
      is_primary: row.querySelector(".image-primary").checked,
      source_url: row.querySelector(".image-source").value,
      filename_base: row.querySelector(".image-filename").value,
      alt_text: row.querySelector(".image-alt").value,
    })),
    specs: [...document.querySelectorAll(".spec-row")].map((row) => ({
      name: row.querySelector(".spec-name").value,
      value: row.querySelector(".spec-value").value,
    })),
  };
}

function addImageRow(image) {
  const row = imageTemplate.content.firstElementChild.cloneNode(true);
  const enabledInput = row.querySelector(".image-enabled");
  const primaryInput = row.querySelector(".image-primary");
  enabledInput.checked = image.enabled ?? true;
  primaryInput.checked = image.is_primary ?? false;
  row.querySelector(".image-source").value = image.source_url || "";
  row.querySelector(".image-filename").value = image.filename_base || "";
  row.querySelector(".image-alt").value = image.alt_text || "";
  row.querySelector(".image-preview").src = image.source_url || "";
  enabledInput.addEventListener("change", ensurePrimaryImage);
  primaryInput.addEventListener("change", () => selectPrimaryImage(row));
  row.querySelector(".order-image-up").addEventListener("click", () => moveImageRow(row, -1));
  row.querySelector(".order-image-down").addEventListener("click", () => moveImageRow(row, 1));
  row.querySelector(".remove-row").addEventListener("click", () => {
    row.remove();
    ensurePrimaryImage();
  });
  imageRows.appendChild(row);
  if (primaryInput.checked && enabledInput.checked) {
    selectPrimaryImage(row);
  } else {
    ensurePrimaryImage();
  }
}

function selectPrimaryImage(row) {
  if (!row.querySelector(".image-enabled").checked) return;
  row.querySelector(".image-primary").checked = true;
  imageRows.prepend(row);
  updateImageControls();
}

function ensurePrimaryImage() {
  const rows = [...imageRows.querySelectorAll(".image-row")];
  const enabledRows = rows.filter((row) => row.querySelector(".image-enabled").checked);
  let primaryRow = enabledRows.find((row) => row.querySelector(".image-primary").checked);

  if (!primaryRow && enabledRows.length) {
    primaryRow = enabledRows[0];
    primaryRow.querySelector(".image-primary").checked = true;
    imageRows.prepend(primaryRow);
  }

  updateImageControls();
}

function moveImageRow(row, direction) {
  const sibling = direction < 0 ? row.previousElementSibling : row.nextElementSibling;
  if (!sibling) return;

  if (direction < 0) {
    imageRows.insertBefore(row, sibling);
  } else {
    imageRows.insertBefore(sibling, row);
  }
  updateImageControls();
}

function updateImageControls() {
  const rows = [...imageRows.querySelectorAll(".image-row")];
  const primaryRow = rows.find((row) => row.querySelector(".image-primary").checked);
  for (const [index, row] of rows.entries()) {
    const enabled = row.querySelector(".image-enabled").checked;
    const primaryInput = row.querySelector(".image-primary");
    primaryInput.disabled = !enabled;
    if (!enabled) primaryInput.checked = false;
    row.classList.toggle("is-primary", primaryInput.checked);
    row.querySelector(".order-image-up").disabled = index === 0 || rows[index - 1] === primaryRow;
    row.querySelector(".order-image-down").disabled = index === rows.length - 1 || row === primaryRow;
  }
}

function addSpecRow(spec) {
  const row = specTemplate.content.firstElementChild.cloneNode(true);
  row.querySelector(".spec-name").value = spec.name || "";
  row.querySelector(".spec-value").value = spec.value || "";
  row.querySelector(".remove-row").addEventListener("click", () => row.remove());
  specRows.appendChild(row);
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join("\n") : data.detail;
    throw new Error(detail || "Request failed");
  }
  return data;
}

function downloadXml() {
  if (!latestXml) return;
  const blob = new Blob([latestXml], { type: "application/xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "document.xml";
  link.click();
  URL.revokeObjectURL(url);
}

function setBusy(text) {
  statusPill.textContent = text;
  for (const button of form.querySelectorAll("button")) button.disabled = true;
}

function setIdle() {
  statusPill.textContent = "Idle";
  for (const button of form.querySelectorAll("button")) button.disabled = false;
  downloadButton.disabled = !latestXml;
  updateImageControls();
}

function setMessage(message, isError = false) {
  messagePanel.textContent = message;
  messagePanel.style.borderColor = isError ? "#a63b32" : "#d7d9d0";
}
