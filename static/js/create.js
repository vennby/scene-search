/* ======================= CREATE PAGE LOGIC ======================= */

let selectedClips = [];
let draggedElement = null;
let draggedIndex = null;

/**
 * Search for similar scenes based on user query
 */
function searchSimilarScenes() {
  const query = document.getElementById("sceneQuery").value.trim();

  if (!query) {
    alert("Please enter a scene description to search");
    return;
  }

  const loadingIndicator = document.getElementById("loadingIndicator");
  const button = document.querySelector(".search-button");

  button.disabled = true;
  loadingIndicator.classList.add("show");

  fetch("/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: query }),
  })
    .then((res) => res.json())
    .then((data) => {
      const results = data.results || [];
      // Filter results with at least 20% similarity
      const filteredResults = results.filter((item) => item.score >= 0.2);
      displayResults(filteredResults);
    })
    .catch((err) => {
      console.error(err);
      alert("Search failed. Please try again.");
    })
    .finally(() => {
      button.disabled = false;
      loadingIndicator.classList.remove("show");
    });
}

/**
 * Display search results as draggable tiles
 */
function displayResults(results) {
  const container = document.getElementById("tilesContainer");
  const resultsSection = document.getElementById("resultsSection");

  // Show results section
  resultsSection.style.display = "block";

  if (results.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1">
        <div class="empty-state-icon">🔍</div>
        <p>No similar scenes found (20%+ match)</p>
      </div>
    `;
    document.getElementById("actionButtons").style.display = "none";
    return;
  }

  container.innerHTML = results
    .map(
      (clip, index) => `
    <div class="clip-tile" draggable="true" data-id="${clip.id}" data-index="${index}">
      <img
        src="/thumbnail/${clip.id}"
        alt="${clip.title}"
        class="clip-thumbnail"
        onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23333%22 width=%22400%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 font-size=%2224%22 fill=%22%23999%22 text-anchor=%22middle%22 dy=%22.3em%22%3ENo thumbnail%3C/text%3E%3C/svg%3E'"
      />
      <span class="similarity-badge">${(clip.score * 100).toFixed(0)}%</span>
      <button class="remove-button" onclick="event.stopPropagation(); removeFromSequence('${clip.id}')">×</button>
      <div class="clip-overlay">
        <div class="clip-title-overlay">${clip.title}</div>
        ${
          clip.tags
            ? `
          <div class="clip-tags-overlay">
            ${clip.tags
              .split(",")
              .slice(0, 3)
              .map((tag) => `<span class="tag-small">${tag.trim()}</span>`)
              .join("")}
          </div>
        `
            : ""
        }
      </div>
    </div>
  `
    )
    .join("");

  setupDragAndDrop();
  document.getElementById("actionButtons").style.display = "flex";
}

/**
 * Setup drag and drop event listeners for tiles
 */
function setupDragAndDrop() {
  const tiles = document.querySelectorAll(".clip-tile");

  tiles.forEach((tile) => {
    tile.addEventListener("dragstart", handleDragStart);
    tile.addEventListener("dragover", handleDragOver);
    tile.addEventListener("drop", handleDrop);
    tile.addEventListener("dragend", handleDragEnd);
    tile.addEventListener("dragenter", handleDragEnter);
    tile.addEventListener("dragleave", handleDragLeave);
  });
}

/**
 * Handle drag start event
 */
function handleDragStart(e) {
  draggedElement = this;
  draggedElement.classList.add("dragging");
  e.dataTransfer.effectAllowed = "move";
}

/**
 * Handle drag over event
 */
function handleDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
}

/**
 * Handle drag enter event
 */
function handleDragEnter(e) {
  if (this !== draggedElement) {
    this.style.opacity = "0.7";
  }
}

/**
 * Handle drag leave event
 */
function handleDragLeave(e) {
  this.style.opacity = "1";
}

/**
 * Handle drop event and reorder tiles
 */
function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();

  if (this !== draggedElement) {
    const container = document.getElementById("tilesContainer");
    const allTiles = Array.from(container.children);
    const draggedIndex = allTiles.indexOf(draggedElement);
    const targetIndex = allTiles.indexOf(this);

    if (draggedIndex < targetIndex) {
      this.parentNode.insertBefore(draggedElement, this.nextSibling);
    } else {
      this.parentNode.insertBefore(draggedElement, this);
    }
  }

  this.style.opacity = "1";
}

/**
 * Handle drag end event
 */
function handleDragEnd(e) {
  draggedElement.classList.remove("dragging");
  document.querySelectorAll(".clip-tile").forEach((tile) => {
    tile.style.opacity = "1";
  });
}

/**
 * Remove a clip from the sequence
 */
function removeFromSequence(clipId) {
  const container = document.getElementById("tilesContainer");
  const tile = container.querySelector(`[data-id="${clipId}"]`);
  if (tile) {
    tile.remove();
    updateSequenceInfo();

    const tiles = container.querySelectorAll(".clip-tile");
    if (tiles.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1">
          <div class="empty-state-icon">🎬</div>
          <p>Search for scenes to get started</p>
        </div>
      `;
      document.getElementById("actionButtons").style.display = "none";
    }
  }
}

/**
 * Update the sequence info counter
 */
function updateSequenceInfo() {
  const container = document.getElementById("tilesContainer");
  const tiles = container.querySelectorAll(".clip-tile");
  const count = tiles.length;

  if (count > 0) {
    document.getElementById("sequenceInfo").style.display = "block";
    document.getElementById("sequenceCount").textContent = count;
  } else {
    document.getElementById("sequenceInfo").style.display = "none";
  }
}

/**
 * Get the current sequence order
 */
function getSequenceOrder() {
  const container = document.getElementById("tilesContainer");
  const tiles = Array.from(container.querySelectorAll(".clip-tile"));
  return tiles.map((tile) => ({
    id: tile.dataset.id,
    title: tile.querySelector(".clip-title-overlay")?.textContent || "",
  }));
}

/**
 * Save the sequence to the database
 */
function saveSequence() {
  const sequence = getSequenceOrder();

  if (sequence.length === 0) {
    alert("Please select at least one scene to save");
    return;
  }

  const sequenceName = prompt("Enter a name for this sequence:", "My Sequence");

  if (!sequenceName) {
    return;
  }

  const description = prompt(
    "Add an optional description (press Enter to skip):",
    ""
  );

  const button = document.querySelector(".btn-primary");
  button.disabled = true;
  button.textContent = "Saving...";

  fetch("/api/sequence/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: sequenceName,
      description: description || "",
      clips: sequence,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.redirect) {
        alert(
          `Sequence "${sequenceName}" saved with ${sequence.length} clips!`
        );
        window.location.href = data.redirect;
      } else {
        alert("Error: " + (data.error || "Unknown error"));
      }
    })
    .catch((err) => {
      console.error(err);
      alert("Error saving sequence. Please try again.");
    })
    .finally(() => {
      button.disabled = false;
      button.textContent = "Save Sequence";
    });
}

/**
 * Clear all selected clips
 */
function clearSequence() {
  if (
    confirm(
      "Are you sure you want to clear all selected clips? This cannot be undone."
    )
  ) {
    document.getElementById("tilesContainer").innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1">
        <div class="empty-state-icon">🎬</div>
        <p>Search for scenes to get started</p>
      </div>
    `;
    document.getElementById("actionButtons").style.display = "none";
    document.getElementById("sequenceInfo").style.display = "none";
    document.getElementById("sceneQuery").value = "";
    selectedClips = [];
  }
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  // Enter key support for search
  const sceneQueryInput = document.getElementById("sceneQuery");
  if (sceneQueryInput) {
    sceneQueryInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        searchSimilarScenes();
      }
    });
  }
});
