document.addEventListener("DOMContentLoaded", () => {
    // ── 1. STAR RATING WIDGETS WITH 0.5 SUPPORT ────────────────────────
    const starWidgets = document.querySelectorAll(".star-rating-widget");

    function renderWidgetStars(widget, rating) {
        const slots = widget.querySelectorAll(".star-slot");
        const hiddenInput = widget.querySelector('input[type="hidden"]');
        const scoreDisplay = widget.parentElement.querySelector(".score-display");

        slots.forEach((slot) => {
            const index = parseInt(slot.dataset.starIndex, 10);
            const fillWrap = slot.querySelector(".star-fill-wrap");

            if (rating >= index) {
                fillWrap.style.width = "100%";
            } else if (rating === index - 0.5) {
                fillWrap.style.width = "50%";
            } else {
                fillWrap.style.width = "0%";
            }
        });

        if (scoreDisplay) {
            if (rating > 0) {
                scoreDisplay.textContent = `${rating} ★`;
                scoreDisplay.classList.add("visible");
            } else {
                scoreDisplay.textContent = "";
                scoreDisplay.classList.remove("visible");
            }
        }
    }

    starWidgets.forEach((widget) => {
        const slots = widget.querySelectorAll(".star-slot");
        const hiddenInput = widget.querySelector('input[type="hidden"]');

        const initialVal = parseFloat(hiddenInput.value) || 0;
        if (initialVal > 0) {
            renderWidgetStars(widget, initialVal);
        }

        slots.forEach((slot) => {
            const leftHalf = slot.querySelector(".star-half-left");
            const rightHalf = slot.querySelector(".star-half-right");

            [leftHalf, rightHalf].forEach((half) => {
                const val = parseFloat(half.dataset.value);

                half.addEventListener("mouseenter", () => {
                    renderWidgetStars(widget, val);
                });

                half.addEventListener("click", () => {
                    hiddenInput.value = val;
                    widget.dataset.selectedRating = val;
                    renderWidgetStars(widget, val);
                });
            });
        });

        widget.addEventListener("mouseleave", () => {
            const currentRating = parseFloat(widget.dataset.selectedRating || hiddenInput.value || 0);
            renderWidgetStars(widget, currentRating);
        });
    });

    // Helper to manually set a star rating widget from JS (used during Edit)
    function setWidgetRating(widgetId, score) {
        const widget = document.querySelector(`.star-rating-widget[data-rating-id="${widgetId}"]`);
        if (!widget) return;
        const hiddenInput = widget.querySelector('input[type="hidden"]');
        hiddenInput.value = score;
        widget.dataset.selectedRating = score;
        renderWidgetStars(widget, score);
    }

    // ── 2. DYNAMIC CANDIDATE DROPDOWN BY ROOM & ROUND ──────────────────
    const candidateSelect = document.getElementById("candidateSelect");
    const roomHint = document.getElementById("roomFilterHint");
    const roomRadios = document.querySelectorAll('input[name="room"]');
    const roundRadios = document.querySelectorAll('input[name="round"]');

    function getSelectedRoom() {
        const checked = document.querySelector('input[name="room"]:checked');
        return checked ? checked.value : "Tinker Toys";
    }

    function getSelectedRound() {
        const checked = document.querySelector('input[name="round"]:checked');
        return checked ? checked.value : "Round 1";
    }

    function updateCandidateDropdown(candidateToSelect = null) {
        if (!candidateSelect || !window.ROOM_ASSIGNMENTS) return;

        const currentRoom = getSelectedRoom();
        const currentRound = getSelectedRound();

        const roundData = window.ROOM_ASSIGNMENTS[currentRound] || {};
        const candidatesInRoom = roundData[currentRoom] || [];

        candidateSelect.innerHTML = "";

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.disabled = true;
        defaultOption.textContent = `-- Select candidate in ${currentRoom} (${currentRound}) --`;
        candidateSelect.appendChild(defaultOption);

        if (roomHint) {
            roomHint.textContent = `${candidatesInRoom.length} students assigned to ${currentRoom} in ${currentRound}`;
        }

        const observed = window.OBSERVED_NAMES || [];

        candidatesInRoom.forEach((name) => {
            const opt = document.createElement("option");
            opt.value = name;
            const isObserved = observed.includes(name);
            opt.textContent = isObserved ? `${name} ✓ (Evaluated)` : name;
            candidateSelect.appendChild(opt);
        });

        if (candidateToSelect && candidatesInRoom.includes(candidateToSelect)) {
            candidateSelect.value = candidateToSelect;
        } else {
            defaultOption.selected = true;
        }
    }

    // Update candidate dropdown whenever room or round changes
    roomRadios.forEach((r) => r.addEventListener("change", () => updateCandidateDropdown()));
    roundRadios.forEach((r) => r.addEventListener("change", () => updateCandidateDropdown()));

    // Initial dropdown population
    updateCandidateDropdown();

    // ── 3. EDIT OBSERVATION INLINE ──────────────────────────────────────
    const editButtons = document.querySelectorAll(".btn-edit");
    const editIdInput = document.getElementById("editIdInput");
    const editingBanner = document.getElementById("editingBanner");
    const editingCandidateName = document.getElementById("editingCandidateName");
    const cancelEditBtn = document.getElementById("cancelEditBtn");
    const submitFormBtn = document.getElementById("submitFormBtn");
    const assessmentHeader = document.getElementById("assessmentSectionHeader");
    const commentsInput = document.getElementById("commentsInput");
    const observerNameInput = document.getElementById("observerName");

    editButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const obsId = btn.dataset.id;
            const candidate = btn.dataset.candidate;
            const observer = btn.dataset.observer;
            const room = btn.dataset.room;
            const round = btn.dataset.round;
            const teamwork = parseFloat(btn.dataset.teamwork) || 0;
            const initiative = parseFloat(btn.dataset.initiative) || 0;
            const personalRep = parseFloat(btn.dataset.personalRep) || 0;
            const workWith = btn.dataset.workWith || "Yes";
            const comments = btn.dataset.comments || "";

            // 1. Set edit ID
            editIdInput.value = obsId;

            // 2. Pre-fill observer
            if (observerNameInput && observer) {
                observerNameInput.value = observer;
            }

            // 3. Set Room and Round radio buttons
            const targetRoomRadio = document.querySelector(`input[name="room"][value="${room}"]`);
            if (targetRoomRadio) targetRoomRadio.checked = true;

            const targetRoundRadio = document.querySelector(`input[name="round"][value="${round}"]`);
            if (targetRoundRadio) targetRoundRadio.checked = true;

            // 4. Refresh dropdown to this room/round and select candidate
            updateCandidateDropdown(candidate);

            // 5. Pre-fill star widgets
            setWidgetRating("teamwork", teamwork);
            setWidgetRating("initiative", initiative);
            setWidgetRating("personal_rep", personalRep);

            // 6. Pre-fill work_with
            const targetWorkWith = document.querySelector(`input[name="work_with"][value="${workWith}"]`);
            if (targetWorkWith) targetWorkWith.checked = true;

            // 7. Pre-fill comments
            if (commentsInput) {
                commentsInput.value = comments;
            }

            // 8. Update UI mode to Edit
            if (editingBanner) {
                editingBanner.style.display = "flex";
                if (editingCandidateName) editingCandidateName.textContent = candidate;
            }
            if (submitFormBtn) {
                submitFormBtn.textContent = `Update Evaluation for ${candidate}`;
                submitFormBtn.classList.add("btn-update-mode");
            }

            // 9. Scroll smoothly to assessment section
            if (assessmentHeader) {
                assessmentHeader.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    if (cancelEditBtn) {
        cancelEditBtn.addEventListener("click", () => {
            editIdInput.value = "";
            if (editingBanner) editingBanner.style.display = "none";
            if (submitFormBtn) {
                submitFormBtn.textContent = "Save Candidate Evaluation";
                submitFormBtn.classList.remove("btn-update-mode");
            }
            // Reset fields
            if (commentsInput) commentsInput.value = "";
            setWidgetRating("teamwork", 0);
            setWidgetRating("initiative", 0);
            setWidgetRating("personal_rep", 0);
            updateCandidateDropdown();
        });
    }

    // ── 4. ROUND TABS SWITCHER ─────────────────────────────────────────
    const tabButtons = document.querySelectorAll(".round-tab-btn");
    const roundBlocks = document.querySelectorAll(".round-table-card");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            tabButtons.forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");

            const target = btn.dataset.target;
            roundBlocks.forEach((block) => {
                if (target === "all" || block.dataset.roundId === target) {
                    block.style.display = "block";
                } else {
                    block.style.display = "none";
                }
            });
        });
    });
});
