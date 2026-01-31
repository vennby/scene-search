/* ======================= SEARCH PAGE LOGIC ======================= */

let teluguEnabled = false;

/**
 * Navigate to edit page for a clip
 */
function editClip(clipId) {
  window.location.href = `/edit/${clipId}`;
}

/**
 * Delete a clip from the database
 */
function deleteClip(clipId) {
  if (
    !confirm(
      "Are you sure you want to delete this item? This action cannot be undone."
    )
  ) {
    return;
  }

  fetch(`/delete/${clipId}`, {
    method: "POST",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.redirect) {
        window.location.href = data.redirect;
      } else {
        alert(data.message || "Deleted!");
      }
    })
    .catch((err) => {
      console.error(err);
      alert("Error deleting item.");
    });
}

/**
 * Perform semantic search
 */
function performSemanticSearch(query) {
  console.log("🔍 Searching for:", query);
  fetch("/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: query }),
  })
    .then((res) => {
      console.log("📨 Response status:", res.status);
      return res.json();
    })
    .then((data) => {
      console.log("📦 Response data:", data);
      if (data.results) {
        console.log("✓ Found", data.results.length, "results");
        displaySearchResults(data.results);
      } else {
        console.log("✗ No results field in response");
        displaySearchResults([]);
      }
    })
    .catch((err) => {
      console.error("❌ Search error:", err);
      alert("Search failed");
    });
}

/**
 * Display search results in the clip list
 */
function displaySearchResults(results) {
  const clipList = document.getElementById("clipList");

  if (results.length === 0) {
    clipList.innerHTML =
      '<div style="color: #b8b6b0; text-align: center">No results found.</div>';
    return;
  }

  let html = "";
  results.forEach((item) => {
    const score = (item.score * 100).toFixed(1);
    html += `
      <div class="clip-item">
        <div class="clip-thumb-container">
          ${item.file_type.toLowerCase() === 'video' ? `<img class="clip-thumb" src="/thumbnail/${item.id}" alt="${item.title}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23333%22 width=%22400%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 font-size=%2224%22 fill=%22%23999%22 text-anchor=%22middle%22 dy=%22.3em%22%3ENo thumbnail%3C/text%3E%3C/svg%3E'" />` : `<img class="clip-thumb" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect fill='%23333' width='400' height='300'/%3E%3Ctext x='50%25' y='50%25' font-size='24' fill='%23999' text-anchor='middle' dy='.3em'%3EDocument%3C/text%3E%3C/svg%3E" alt="document" />`}
          <span class="file-type-badge">${item.file_type}</span>
        </div>
        <div>
          <div class="clip-title">${item.title}</div>
          <div class="clip-meta">
            Saved: ${new Date(item.timestamp).toLocaleString()} | Match: ${score}%
          </div>
          <div class="clip-desc">${item.description}</div>
          <div class="tags">
            ${
              item.tags
                ? item.tags
                    .split(",")
                    .map((tag) => `<span class="tag">${tag.trim()}</span>`)
                    .join("")
                : ""
            }
          </div>
          <button class="clip-action" onclick="editClip('${item.id}')">Edit</button>
          <button
            class="clip-action delete"
            onclick="deleteClip('${item.id}')"
          >
            Delete
          </button>
        </div>
      </div>
    `;
  });

  clipList.innerHTML = html;
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("searchInput");
  const toggle = document.getElementById("langToggle");

  // Search on Enter key
  input.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
      const query = input.value.trim();
      if (query) {
        performSemanticSearch(query);
      }
    }
  });

  // Telugu language toggle
  toggle.addEventListener("click", () => {
    teluguEnabled = !teluguEnabled;
    toggle.classList.toggle("active", teluguEnabled);
  });

  // Transliterate on space (Telugu mode)
  input.addEventListener("keydown", (e) => {
    if (!teluguEnabled) return;

    // Only transliterate on SPACE — NOT Enter
    if (e.key === " ") {
      const words = input.value.split(/\s+/);
      const lastIndex = words.length - 1;
      const lastWord = words[lastIndex];

      if (/^[a-zA-Z]+$/.test(lastWord)) {
        words[lastIndex] = Sanscript.t(lastWord, "itrans", "telugu");
        input.value = words.join(" ");
      }
    }
  });
});
