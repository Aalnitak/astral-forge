// --- HTMX Global Init -------------------------------------------------------

// CSRF for unsafe methods
document.addEventListener("htmx:configRequest", (event) => {
  const verb = (event.detail.verb || "").toUpperCase();
  if (!["POST", "PUT", "PATCH", "DELETE"].includes(verb)) return;

  let token = null;
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && meta.content) token = meta.content;
  if (!token) {
    const m = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
    if (m) token = m.pop();
  }
  if (token) event.detail.headers["X-CSRFToken"] = token;
});

// Global & per-element loading indicators
document.addEventListener("htmx:beforeRequest", (e) => {
  document.documentElement.classList.add("htmx-request");
  if (e.target) e.target.classList.add("is-loading");
});
document.addEventListener("htmx:afterRequest", (e) => {
  document.documentElement.classList.remove("htmx-request");
  if (e.target) e.target.classList.remove("is-loading");
});

// Redirect / Refresh
document.addEventListener("htmx:afterOnLoad", (e) => {
  const redirect = e.detail.xhr.getResponseHeader("HX-Redirect");
  if (redirect) {
    window.location.href = redirect;
    return;
  }
  const refresh = e.detail.xhr.getResponseHeader("HX-Refresh");
  if (refresh && refresh.toLowerCase() !== "false") {
    window.location.reload();
  }
});

// Prevent double submits
document.addEventListener("htmx:beforeRequest", (e) => {
  const submitter = e.detail?.requestConfig?.submitter;
  if (submitter && submitter instanceof HTMLElement) {
    submitter.setAttribute("disabled", "true");
    submitter.setAttribute("aria-busy", "true");
  }
});
document.addEventListener("htmx:afterRequest", (e) => {
  const submitter = e.detail?.requestConfig?.submitter;
  if (submitter && submitter instanceof HTMLElement) {
    submitter.removeAttribute("disabled");
    submitter.removeAttribute("aria-busy");
  }
});

// Optional: keep only console diagnostics for non-2xx responses
document.addEventListener("htmx:responseError", (e) => {
  const status = e.detail.xhr?.status || 0;
  console.error("HTMX error", status, e.detail.xhr?.responseText);
});
