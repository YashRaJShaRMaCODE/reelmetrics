const form = document.querySelector("#lead-form");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const status = document.querySelector("#lead-status");
  const button = form.querySelector("button");
  button.disabled = true;
  status.textContent = "Submitting…";
  try {
    const response = await fetch(form.dataset.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project: "reelmetrics",
        email: form.elements.email.value.trim(),
        consent: form.elements.consent.checked,
        source: "catalog-quality-lab-site",
        website: "",
      }),
    });
    if (!response.ok) throw new Error("request failed");
    form.reset();
    status.textContent = "Check your email to confirm your signup.";
  } catch {
    status.textContent = "Signup is temporarily unavailable.";
  } finally {
    button.disabled = false;
  }
});

const relatedBox = document.querySelector("#related-products");
const relatedConsent = document.querySelector("#related-consent");
const relatedStatus = document.querySelector("#related-status");
const relatedList = document.querySelector("#related-list");

relatedConsent?.addEventListener("change", async () => {
  relatedList.replaceChildren();
  relatedStatus.textContent = "";
  if (!relatedConsent.checked) return;
  relatedStatus.textContent = "Loading suggestions…";
  try {
    const response = await fetch(`${relatedBox.dataset.endpoint}?project=reelmetrics&consent=true`);
    const result = await response.json();
    if (!response.ok) throw new Error("Suggestions unavailable");
    for (const item of result.items || []) {
      const url = new URL(item.url);
      if (url.protocol !== "https:") continue;
      const entry = document.createElement("li");
      const link = document.createElement("a");
      link.href = url.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = item.name;
      entry.append(link, document.createTextNode(` — ${item.reason}`));
      relatedList.append(entry);
    }
    relatedStatus.textContent = relatedList.childElementCount ? "Our other products" : "No related products are available right now.";
  } catch {
    relatedStatus.textContent = "Suggestions are unavailable right now.";
  }
});
