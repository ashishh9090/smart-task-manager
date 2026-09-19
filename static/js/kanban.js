/**
 * Kanban Drag and Drop Logic
 * Uses native HTML5 Drag and Drop API + AJAX to persist task status changes.
 */

document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.kanban-card');
    const columns = document.querySelectorAll('.kanban-column-body');

    let draggedCard = null;

    // Attach event listeners to all draggable cards
    cards.forEach(card => {
        card.setAttribute('draggable', 'true');

        card.addEventListener('dragstart', (e) => {
            draggedCard = card;
            card.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', card.dataset.taskId);
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            draggedCard = null;
        });
    });

    // Attach event listeners to drop zones (columns)
    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            column.classList.add('drag-over');
        });

        column.addEventListener('dragleave', () => {
            column.classList.remove('drag-over');
        });

        column.addEventListener('drop', async (e) => {
            e.preventDefault();
            column.classList.remove('drag-over');

            if (!draggedCard) return;

            const taskId = draggedCard.dataset.taskId;
            const newStatus = column.dataset.status;
            const currentStatus = draggedCard.dataset.status;

            if (newStatus === currentStatus) {
                return; // No status change
            }

            // Move card in DOM optimistically
            column.appendChild(draggedCard);
            draggedCard.dataset.status = newStatus;
            updateColumnCounters();

            // Persist status change to backend API
            try {
                const csrfToken = getCsrfToken();
                const response = await fetch(`/tasks/${taskId}/status/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({ status: newStatus }),
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    showToast(`Task #${taskId} moved to ${data.new_status_display}!`, 'success');
                } else {
                    throw new Error(data.error || 'Failed to update task status.');
                }
            } catch (err) {
                console.error('Kanban update error:', err);
                showToast(err.message || 'Error updating task status. Reloading...', 'error');
                setTimeout(() => window.location.reload(), 1500);
            }
        });
    });

    // Function to recalculate count badges on each column header
    function updateColumnCounters() {
        columns.forEach(col => {
            const status = col.dataset.status;
            const count = col.querySelectorAll('.kanban-card').length;
            const badge = document.getElementById(`count-${status}`);
            if (badge) {
                badge.textContent = count;
            }
        });
    }

    // Quick move button handlers (mobile friendly fallback)
    document.querySelectorAll('.btn-quick-move').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const taskId = btn.dataset.taskId;
            const newStatus = btn.dataset.targetStatus;
            const card = document.getElementById(`task-card-${taskId}`);
            const targetColumn = document.querySelector(`.kanban-column-body[data-status="${newStatus}"]`);

            if (!card || !targetColumn) return;

            targetColumn.appendChild(card);
            card.dataset.status = newStatus;
            updateColumnCounters();

            try {
                const csrfToken = getCsrfToken();
                const response = await fetch(`/tasks/${taskId}/status/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({ status: newStatus }),
                });

                const data = await response.json();
                if (response.ok && data.success) {
                    showToast(`Task #${taskId} moved to ${data.new_status_display}!`, 'success');
                } else {
                    throw new Error(data.error || 'Update failed');
                }
            } catch (err) {
                showToast('Error updating status: ' + err.message, 'error');
                setTimeout(() => window.location.reload(), 1500);
            }
        });
    });
});
