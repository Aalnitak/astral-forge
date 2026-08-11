// toast.js
// Auto-dismiss & utilities for server-rendered daisyUI toasts (alerts) appended via HTMX OOB.
//
// Requirements:
//  - base.html must have a single global host:
//      <div id="toasts" class="mt-[72px] toast toast-end toast-top z-50" hx-swap-oob="true"></div>
//  - Each server-rendered toast is a single .alert element with data-ttl (ms) with a div wrapper for OOB:
//    <div hx-swap-oob="beforeend:#toasts">
//      <div class="alert alert-success">...</div>
//    </div>

(function () {
  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    const host = document.getElementById("toasts");
    if (!host) return;

    // Schedule auto-remove for one alert element
    function schedule(el) {
      const ttl = parseInt(el.getAttribute("data-ttl") || "0", 10);
      if (ttl > 0) {
        // Clear any previous timer on re-attachment
        if (el._toastTimer) clearTimeout(el._toastTimer);
        el._toastTimer = setTimeout(() => {
          // Defensive: ensure still in DOM
          if (el && el.parentNode) el.remove();
        }, ttl);
      }
    }

    // Pause auto-dismiss on hover, resume on mouseleave
    function bindHoverPause(el) {
      el.addEventListener("mouseenter", () => {
        if (el._toastTimer) {
          clearTimeout(el._toastTimer);
          el._toastTimer = null;
        }
      });
      el.addEventListener("mouseleave", () => {
        const ttl = parseInt(el.getAttribute("data-ttl") || "0", 10);
        if (ttl > 0) {
          el._toastTimer = setTimeout(() => {
            if (el && el.parentNode) el.remove();
          }, 1500);
        }
      });
    }

    // Delegate close button clicks (e.g., the ✕ button inside .alert)
    host.addEventListener("click", (e) => {
      const btn = e.target.closest(".toast-close,[data-toast-close]");
      if (btn) {
        const alert = btn.closest(".alert");
        if (alert) alert.remove();
      }
    });

    // Initialize existing alerts (if any)
    host.querySelectorAll(".alert").forEach((el) => {
      schedule(el);
      bindHoverPause(el);
    });

    // Observe future alerts appended via OOB swaps
    const obs = new MutationObserver((mutations) => {
      for (const m of mutations) {
        for (const node of m.addedNodes) {
          if (node.nodeType === 1 && node.classList.contains("alert")) {
            schedule(node);
            bindHoverPause(node);
          }
        }
      }
    });
    obs.observe(host, { childList: true });
  });
})();
