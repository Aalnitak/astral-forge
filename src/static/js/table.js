(function () {
  function openDropdown(dropdown) {
    setDropdownOpen(dropdown, true);
  }

  function closeDropdown(dropdown) {
    setDropdownOpen(dropdown, false);
  }

  function setDropdownOpen(dropdown, isOpen) {
    dropdown.classList.toggle("dropdown-open", isOpen);

    const trigger = dropdown.querySelector("[data-dropdown-trigger]");
    if (trigger) trigger.setAttribute("aria-expanded", String(isOpen));

    if (!isOpen) resetPanels(dropdown);
  }

  function resetPanels(dropdown) {
    const menu = dropdown.querySelector("[data-filter-menu]");
    if (menu) menu.classList.remove("hidden");
    dropdown.querySelectorAll("[data-filter-panel]").forEach((panel) => {
      panel.classList.add("hidden");
    });
  }

  function showPanel(dropdown, field) {
    const menu = dropdown.querySelector("[data-filter-menu]");
    if (menu) menu.classList.add("hidden");
    dropdown.querySelectorAll("[data-filter-panel]").forEach((panel) => {
      panel.classList.toggle("hidden", panel.dataset.filterPanel !== field);
    });
  }

  function addChip(fieldEl) {
    const input = fieldEl.querySelector("[data-chip-input]");
    const value = input.value.trim();
    if (!value) return;

    const template = fieldEl.querySelector("[data-chip-template]");
    const chip = template.content.firstElementChild.cloneNode(true);
    chip.querySelector("input").value = value;
    chip.querySelector("[data-chip-label]").textContent = value;
    chip.querySelector("[data-chip-remove]").setAttribute("aria-label", "Remove " + value);
    fieldEl.querySelector("[data-chip-list]").appendChild(chip);

    input.value = "";
    input.focus();
  }

  document.addEventListener("click", (event) => {
    document.querySelectorAll(".dropdown.dropdown-open").forEach((dropdown) => {
      if (!dropdown.contains(event.target)) closeDropdown(dropdown);
    });

    const trigger = event.target.closest("[data-dropdown-trigger]");
    if (trigger) {
      const dropdown = trigger.closest(".dropdown");
      if (dropdown.classList.contains("dropdown-open")) closeDropdown(dropdown);
      else openDropdown(dropdown);
      return;
    }

    const panelOpener = event.target.closest("[data-filter-open]");
    if (panelOpener) {
      showPanel(panelOpener.closest(".dropdown"), panelOpener.dataset.filterOpen);
      return;
    }

    const back = event.target.closest("[data-filter-back]");
    if (back) {
      resetPanels(back.closest(".dropdown"));
      return;
    }

    const close = event.target.closest("[data-filter-close]");
    if (close) {
      closeDropdown(close.closest(".dropdown"));
      return;
    }

    const add = event.target.closest("[data-chip-add]");
    if (add) {
      addChip(add.closest("[data-chip-field]"));
      return;
    }

    const remove = event.target.closest("[data-chip-remove]");
    if (remove) {
      remove.closest("[data-chip]").remove();
      return;
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const input = event.target.closest("[data-chip-input]");
    if (!input) return;
    event.preventDefault();
    addChip(input.closest("[data-chip-field]"));
  });
})();
