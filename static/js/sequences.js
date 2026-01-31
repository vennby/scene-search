/* ======================= SEQUENCES PAGE LOGIC ======================= */

/**
 * Open modal showing sequence details
 */
function viewSequence(sequenceId) {
  console.log("👁️ Viewing sequence:", sequenceId);

  fetch(`/api/sequence/${sequenceId}`)
    .then((res) => res.json())
    .then((data) => {
      const modal = document.getElementById("modal");
      const title = document.getElementById("modalTitle");
      const desc = document.getElementById("modalDescription");
      const date = document.getElementById("modalDate");
      const clipsContainer = document.getElementById("modalClips");

      title.textContent = data.name;
      desc.textContent = data.description;
      date.textContent = new Date(data.timestamp).toLocaleString();

      let clipsHtml = "";
      data.clips.forEach((clip) => {
        const score = (clip.score * 100).toFixed(1);
        clipsHtml += `
          <div class="modal-clip" style="position: relative; overflow: hidden;">
            <img
              class="modal-clip-thumb"
              src="${clip.id ? `/thumbnail/${clip.id}` : 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23333%22 width=%22400%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 font-size=%2224%22 fill=%22%23999%22 text-anchor=%22middle%22 dy=%22.3em%22%3ENo thumbnail%3C/text%3E%3C/svg%3E'}"
              alt="${clip.title}"
            />
            <div class="modal-clip-info" style="
              position: absolute; 
              bottom: 0; 
              left: 0; 
              right: 0; 
              background: rgba(0, 0, 0, 0.7); 
              color: #f5f3ee; 
              padding: 8px; 
              font-size: 0.9em;
              border-top: 2px solid #c08401;
            ">
              <div style="font-weight: bold;">${clip.title}</div>
              <div style="font-size: 0.8em; color: #b8b6b0;">Match: ${score}%</div>
              ${
                clip.tags
                  ? `<div style="font-size: 0.8em; color: #b8b6b0;">Tags: ${clip.tags}</div>`
                  : ""
              }
            </div>
          </div>
        `;
      });

      clipsContainer.innerHTML = clipsHtml;
      modal.style.display = "flex";
      console.log("✓ Modal opened with", data.clips.length, "clips");
    })
    .catch((err) => {
      console.error("❌ Error fetching sequence:", err);
      alert("Error loading sequence.");
    });
}

/**
 * Close the modal
 */
function closeModal() {
  const modal = document.getElementById("modal");
  modal.style.display = "none";
}

/**
 * Delete a sequence with confirmation
 */
function deleteSequence(sequenceId, sequenceName) {
  if (!confirm(`Are you sure you want to delete "${sequenceName}"?`)) {
    return;
  }

  fetch(`/api/sequence/${sequenceId}`, {
    method: "DELETE",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        console.log("✓ Sequence deleted");
        location.reload();
      } else {
        alert(data.message || "Error deleting sequence");
      }
    })
    .catch((err) => {
      console.error("❌ Error deleting sequence:", err);
      alert("Error deleting sequence");
    });
}

// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("modal");
  const closeBtn = document.getElementById("closeModal");
  const createBtn = document.getElementById("createBtn");

  // Close modal when X button is clicked
  if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
  }

  // Close modal when clicking outside of modal content
  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Redirect to create page when "Create" button is clicked
  if (createBtn) {
    createBtn.addEventListener("click", () => {
      window.location.href = "/create";
    });
  }
});
