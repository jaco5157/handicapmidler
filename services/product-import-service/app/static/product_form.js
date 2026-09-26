const form = document.querySelector("#product-form");
const imageRows = document.querySelector("#image-rows");
const specRows = document.querySelector("#spec-rows");
const imageTemplate = document.querySelector("#image-row-template");
const specTemplate = document.querySelector("#spec-row-template");
const statusPill = document.querySelector("#status-pill");
const messagePanel = document.querySelector("#message-panel");
const xmlPreview = document.querySelector("#xml-preview");
const downloadButton = document.querySelector("#download-button");
const googlePreview = document.querySelector("#google-preview");
const googlePreviewUrl = document.querySelector("#google-preview-url");
const googlePreviewTitle = document.querySelector("#google-preview-title");
const googlePreviewDescription = document.querySelector("#google-preview-description");
const titleTagCount = document.querySelector("#title-tag-count");
const metaDescriptionCount = document.querySelector("#meta-description-count");
const HMI_SPEC_NAME = "HMI-nr.";

let latestXml = "";
let validationAttempted = false;

document.querySelector("#scrape-button").addEventListener("click", scrapeProduct);
document.querySelector("#refresh-categories-button").addEventListener("click", refreshCategories);
document.querySelector("#preview-button").addEventListener("click", previewProduct);
document.querySelector("#upload-button").addEventListener("click", uploadProduct);
document.querySelector("#download-button").addEventListener("click", downloadXml);
document.querySelector("#add-image").addEventListener("click", () => addImageRow({}));
document.querySelector("#add-spec").addEventListener("click", () => addSpecRow({}));
form.addEventListener("input", refreshValidation);
form.addEventListener("change", refreshValidation);
form.addEventListener("input", updateGooglePreview);

addSpecRow({});
updateGooglePreview();

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
    setHmiSpec(data.hmi_number);
    document.querySelector("#title-tag").value = data.product_name || "";
    updateGooglePreview();

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
  if (!validateProductForm()) return;

  validationAttempted = false;
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

function validateProductForm(focusFirst = true) {
  validationAttempted = true;
  clearValidationErrors();
  updateImageControls();

  const errors = [];
  const requiredControls = [...form.querySelectorAll("input[required], select[required], textarea[required]")];
  for (const control of requiredControls) {
    if (!control.disabled && !control.value.trim()) {
      addFieldValidationError(errors, control, `${fieldLabel(control)} is required.`);
    }
  }

  const supplierUrl = document.querySelector("#supplier-url");
  if (supplierUrl.value.trim() && supplierUrl.validity.typeMismatch) {
    addFieldValidationError(errors, supplierUrl, "Supplier URL must be a valid URL.");
  }

  const productNumber = document.querySelector("#product-number");
  if (productNumber.value.trim() && !/^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/.test(productNumber.value.trim())) {
    addFieldValidationError(errors, productNumber, "Product number must contain only letters, digits, and hyphens.");
  }

  const price = document.querySelector("#price");
  if (price.value.trim() && !isValidPrice(price.value)) {
    addFieldValidationError(errors, price, "Price must be a number greater than zero.");
  }

  validateImages(errors);

  if (!errors.length) {
    statusPill.textContent = "Idle";
    return true;
  }

  statusPill.textContent = "Needs input";
  setMessage(`Please correct the highlighted fields:\n${errors.map(({ message }) => `• ${message}`).join("\n")}`, true);

  if (focusFirst) {
    errors[0].control.scrollIntoView({ behavior: "smooth", block: "center" });
    errors[0].control.focus({ preventScroll: true });
  }
  return false;
}

function validateImages(errors) {
  const rows = [...imageRows.querySelectorAll(".image-row")];
  const enabledRows = rows.filter((row) => row.querySelector(".image-enabled").checked);
  if (!enabledRows.length) {
    addSectionValidationError(
      errors,
      imageRows.closest(".table-wrap"),
      document.querySelector("#add-image"),
      "At least one image must be enabled.",
    );
    return;
  }

  const filenames = new Map();
  for (const row of enabledRows) {
    const rowNumber = rows.indexOf(row) + 1;
    const sourceUrl = row.querySelector(".image-source").value.trim();
    const filename = row.querySelector(".image-filename");

    if (!isHttpUrl(sourceUrl)) {
      addFieldValidationError(errors, filename, `Image ${rowNumber} is missing a valid source URL.`, row);
    }

    if (filename.value.trim()) {
      const normalizedName = normalizeFilename(filename.value);
      if (filenames.has(normalizedName)) {
        const firstFilename = filenames.get(normalizedName);
        addFieldValidationError(errors, firstFilename, "Image filenames must be unique.", firstFilename.closest(".image-row"));
        addFieldValidationError(errors, filename, `Image ${rowNumber} has a duplicate filename.`, row);
      } else {
        filenames.set(normalizedName, filename);
      }
    }
  }
}

function addFieldValidationError(errors, control, message, row = null) {
  control.setAttribute("aria-invalid", "true");
  if (row) row.classList.add("has-validation-error");

  const error = document.createElement("span");
  error.className = "validation-error";
  error.id = `validation-error-${document.querySelectorAll(".validation-error").length + 1}`;
  error.textContent = message;

  const currentDescriptions = control.getAttribute("aria-describedby");
  control.setAttribute("aria-describedby", [currentDescriptions, error.id].filter(Boolean).join(" "));

  const inlineControl = control.closest(".inline-control");
  if (inlineControl) {
    inlineControl.appendChild(error);
  } else {
    control.insertAdjacentElement("afterend", error);
  }
  errors.push({ control, message });
}

function addSectionValidationError(errors, container, control, message) {
  container.classList.add("has-validation-error");
  const error = document.createElement("p");
  error.className = "validation-error section-validation-error";
  error.textContent = message;
  container.appendChild(error);
  errors.push({ control, message });
}

function clearValidationErrors() {
  for (const error of form.querySelectorAll(".validation-error")) error.remove();
  for (const control of form.querySelectorAll('[aria-invalid="true"]')) {
    control.removeAttribute("aria-invalid");
    control.removeAttribute("aria-describedby");
  }
  for (const element of form.querySelectorAll(".has-validation-error")) element.classList.remove("has-validation-error");
}

function refreshValidation() {
  if (validationAttempted) validateProductForm(false);
}

function fieldLabel(control) {
  const label = control.id ? document.querySelector(`label[for="${control.id}"]`) : null;
  if (label) return label.textContent.trim();
  if (control.classList.contains("image-filename")) {
    const rows = [...imageRows.querySelectorAll(".image-row")];
    return `Image ${rows.indexOf(control.closest(".image-row")) + 1} filename`;
  }
  return "This field";
}

function isValidPrice(value) {
  let normalized = value.trim().replaceAll(" ", "");
  if (normalized.includes(",") && normalized.includes(".")) normalized = normalized.replaceAll(".", "");
  normalized = normalized.replace(",", ".");
  const number = Number(normalized);
  return Number.isFinite(number) && number > 0;
}

function isHttpUrl(value) {
  try {
    return ["http:", "https:"].includes(new URL(value).protocol);
  } catch {
    return false;
  }
}

function normalizeFilename(value) {
  return value
    .replaceAll("æ", "ae")
    .replaceAll("ø", "oe")
    .replaceAll("å", "aa")
    .replaceAll("Æ", "Ae")
    .replaceAll("Ø", "Oe")
    .replaceAll("Å", "Aa")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^A-Za-z0-9]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .toLowerCase();
}

function collectDraft() {
  ensurePrimaryImage();
  return {
    source_url: document.querySelector("#supplier-url").value,
    product_name: document.querySelector("#product-name").value,
    product_number: document.querySelector("#product-number").value,
    price: document.querySelector("#price").value,
    category_id: document.querySelector("#category-id").value,
    title_tag: document.querySelector("#title-tag").value,
    custom_product_url: document.querySelector("#custom-product-url").value,
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

function updateGooglePreview() {
  const titleInput = document.querySelector("#title-tag");
  const descriptionInput = document.querySelector("#meta-description");
  const titleLimit = Number(titleInput.dataset.previewMaxlength);
  const descriptionLimit = Number(descriptionInput.dataset.previewMaxlength);
  const title = titleInput.value.trim().slice(0, titleLimit);
  const description = descriptionInput.value.trim().slice(0, descriptionLimit);
  const customUrl = document.querySelector("#custom-product-url").value.trim();
  const storefrontUrl = googlePreview.dataset.storefrontUrl.replace(/\/+$/, "");
  const storefront = new URL(storefrontUrl);
  const urlParts = [storefront.hostname, "shop"];
  if (customUrl) urlParts.push(customUrl.replace(/^\/+|\/+$/g, ""));

  googlePreviewUrl.textContent = urlParts.join(" › ");
  googlePreviewTitle.textContent = title || "Product title";
  googlePreviewDescription.textContent = description || "The meta description will appear here.";
  titleTagCount.textContent = titleInput.value.length;
  metaDescriptionCount.textContent = descriptionInput.value.length;
  titleTagCount.closest(".field-help").classList.toggle("is-over-limit", titleInput.value.length > titleLimit);
  metaDescriptionCount
    .closest(".field-help")
    .classList.toggle("is-over-limit", descriptionInput.value.length > descriptionLimit);
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
  if (row === imageRows.firstElementChild) {
    updateImageControls();
    return;
  }
  animateImageReorder(row, -1, () => imageRows.prepend(row));
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

  animateImageReorder(row, direction, () => {
    if (direction < 0) {
      imageRows.insertBefore(row, sibling);
    } else {
      imageRows.insertBefore(sibling, row);
    }
  });
}

function animateImageReorder(movedRow, direction, reorder) {
  const rows = [...imageRows.querySelectorAll(".image-row")];
  const previousPositions = new Map(rows.map((row) => [row, row.getBoundingClientRect().top]));

  reorder();
  updateImageControls();

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  for (const row of rows) {
    const distance = previousPositions.get(row) - row.getBoundingClientRect().top;
    if (!distance) continue;
    row.animate(
      [
        { transform: `translateY(${distance}px)` },
        { transform: "translateY(0)" },
      ],
      {
        duration: row === movedRow ? 460 : 380,
        easing: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    );
  }

  const animationClass = direction < 0 ? "moved-up" : "moved-down";
  movedRow.classList.remove("moved-up", "moved-down");
  void movedRow.offsetWidth;
  movedRow.classList.add(animationClass);
  window.setTimeout(() => movedRow.classList.remove(animationClass), 650);
}

function updateImageControls() {
  const rows = [...imageRows.querySelectorAll(".image-row")];
  const primaryRow = rows.find((row) => row.querySelector(".image-primary").checked);
  for (const [index, row] of rows.entries()) {
    const enabled = row.querySelector(".image-enabled").checked;
    const primaryInput = row.querySelector(".image-primary");
    row.querySelector(".image-filename").required = enabled;
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
  return row;
}

function setHmiSpec(hmiNumber) {
  const value = String(hmiNumber || "").trim();
  const matchingRows = [...specRows.querySelectorAll(".spec-row")].filter(
    (row) => row.querySelector(".spec-name").value.trim().toLowerCase() === HMI_SPEC_NAME.toLowerCase(),
  );

  if (!value) {
    for (const row of matchingRows) row.remove();
    return;
  }

  let row = matchingRows.shift();
  if (!row) {
    row = [...specRows.querySelectorAll(".spec-row")].find(
      (candidate) =>
        !candidate.querySelector(".spec-name").value.trim() && !candidate.querySelector(".spec-value").value.trim(),
    );
  }
  if (!row) row = addSpecRow({});

  row.querySelector(".spec-name").value = HMI_SPEC_NAME;
  row.querySelector(".spec-value").value = value;
  for (const duplicate of matchingRows) duplicate.remove();
  specRows.prepend(row);
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
