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
