/* ======================= DROPDOWN FUNCTIONALITY ======================= */

/**
 * Initialize dropdown menu
 * Marks the current page in the dropdown as active
 */
function initializeDropdown() {
  document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname;
    const dropdownItems = document.querySelectorAll(".dropdown-item");
    
    dropdownItems.forEach((item) => {
      if (item.getAttribute("href") === currentPath) {
        item.classList.add("active");
      }
    });
  });
}

// Initialize on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeDropdown);
} else {
  initializeDropdown();
}
