(() => {
  const board = document.querySelector('[data-task-board]');

  if (!board) {
    return;
  }

  let draggedCard = null;
  let dropIndicator = null;

  const getCards = (column) => Array.from(
    column.querySelectorAll('.task-card[draggable="true"]'),
  );

  const getAfterCard = (list, pointerY) => {
    return getCards(list.closest('.task-column')).reduce(
      (closest, card) => {
        if (card === draggedCard) {
          return closest;
        }

        const box = card.getBoundingClientRect();
        const distance = pointerY - box.top - box.height / 2;
        if (distance < 0 && distance > closest.distance) {
          return { distance, card };
        }
        return closest;
      },
      { distance: Number.NEGATIVE_INFINITY, card: null },
    ).card;
  };

  const clearIndicator = () => {
    if (dropIndicator) {
      dropIndicator.remove();
      dropIndicator = null;
    }
  };

  const placeIndicator = (list, pointerY) => {
    clearIndicator();
    dropIndicator = document.createElement('div');
    dropIndicator.className = 'task-drop-indicator';
    const afterCard = getAfterCard(list, pointerY);
    list.insertBefore(dropIndicator, afterCard);
  };

  const resetDragState = () => {
    clearIndicator();
    board.querySelectorAll('.is-dragging, .is-drop-target').forEach((element) => {
      element.classList.remove('is-dragging', 'is-drop-target');
    });
    draggedCard = null;
  };

  board.querySelectorAll('.task-card[draggable="true"]').forEach((card) => {
    card.addEventListener('dragstart', (event) => {
      draggedCard = card;
      card.classList.add('is-dragging');
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', card.dataset.taskId);
      const transparentDragImage = document.createElement('canvas');
      transparentDragImage.width = 1;
      transparentDragImage.height = 1;
      event.dataTransfer.setDragImage(transparentDragImage, 0, 0);
    });

    card.addEventListener('dragend', resetDragState);
  });

  board.querySelectorAll('.task-column').forEach((column) => {
    const list = column.querySelector('.task-column-list');

    column.addEventListener('dragover', (event) => {
      if (!draggedCard) {
        return;
      }

      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
      column.classList.add('is-drop-target');
      placeIndicator(list, event.clientY);
    });

    column.addEventListener('dragleave', (event) => {
      if (!column.contains(event.relatedTarget)) {
        column.classList.remove('is-drop-target');
        clearIndicator();
      }
    });

    column.addEventListener('drop', async (event) => {
      event.preventDefault();
      if (!draggedCard || !dropIndicator) {
        resetDragState();
        return;
      }

      const beforeTask = dropIndicator.nextElementSibling;
      const body = new URLSearchParams({
        column: column.dataset.columnKey,
        before_task_id: beforeTask?.dataset.taskId || '',
      });
      const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]')?.value;
      if (csrfToken) {
        body.set('csrfmiddlewaretoken', csrfToken);
      }

      const dragUrl = draggedCard.dataset.dragUrl;
      try {
        const response = await fetch(dragUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken || '',
            'X-Requested-With': 'XMLHttpRequest',
          },
          body,
        });
        if (!response.ok) {
          throw new Error('Não foi possível mover a tarefa.');
        }
        window.location.reload();
      } catch (error) {
        resetDragState();
      }
    });
  });
})();
