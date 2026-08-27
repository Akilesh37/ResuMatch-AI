/**
 * Queue Monitor Component - Real-time SSE worker task stream & animated progress
 */
class QueueMonitor {
    constructor(app) {
        this.app = app;
        this.tasks = new Map();
        this.eventSource = null;

        this.initElements();
        this.startSSE();
    }

    initElements() {
        this.statTotal = document.getElementById('queue-stat-total');
        this.statQueued = document.getElementById('queue-stat-queued');
        this.statProcessing = document.getElementById('queue-stat-processing');
        this.statCompleted = document.getElementById('queue-stat-completed');
        this.tasksContainer = document.getElementById('tasks-list-container');
    }

    startSSE() {
        this.eventSource = API.subscribeQueueStream(
            (data) => this.handleSSEMessage(data),
            (err) => {
                console.warn('SSE connection warning, will auto-reconnect...', err);
            }
        );
    }

    handleSSEMessage(data) {
        if (data.event === 'INITIAL_STATE') {
            if (data.tasks) {
                data.tasks.forEach(t => this.tasks.set(t.id, t));
            }
            this.updateStats(data.stats);
            this.renderTasks();
        } else if (data.event === 'TASK_ENQUEUED' || data.event === 'TASK_PROGRESS') {
            const task = data.task;
            const prev = this.tasks.get(task.id);
            this.tasks.set(task.id, task);

            this.renderTasks();
            this.recalculateStats();

            // If task just completed, refresh rankings leaderboard
            if (task.status === 'COMPLETED' && (!prev || prev.status !== 'COMPLETED')) {
                this.app.onTaskCompleted(task);
            }
        }
    }

    recalculateStats() {
        const list = Array.from(this.tasks.values());
        const stats = {
            total: list.length,
            queued: list.filter(t => t.status === 'QUEUED').length,
            processing: list.filter(t => !['QUEUED', 'COMPLETED', 'FAILED'].includes(t.status)).length,
            completed: list.filter(t => t.status === 'COMPLETED').length
        };
        this.updateStats(stats);
    }

    updateStats(stats) {
        if (!stats) return;
        this.statTotal.textContent = stats.total || 0;
        this.statQueued.textContent = stats.queued || 0;
        this.statProcessing.textContent = stats.processing || 0;
        this.statCompleted.textContent = stats.completed || 0;

        // Top bar updates
        const statOcr = document.getElementById('stat-ocr-count');
        if (statOcr && stats.completed > 0) {
            statOcr.textContent = `${stats.completed} Processed`;
        }
    }

    renderTasks() {
        const taskList = Array.from(this.tasks.values()).reverse();
        if (taskList.length === 0) {
            this.tasksContainer.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="inbox"></i>
                    <h3>Resume Queue is Empty</h3>
                    <p>No active or pending resume processing tasks.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        this.tasksContainer.innerHTML = taskList.map(task => {
            const stageClass = `stage-${task.status.toLowerCase()}`;
            const isWorking = !['QUEUED', 'COMPLETED', 'FAILED'].includes(task.status);

            return `
                <div class="task-card">
                    <div class="task-card-header">
                        <div class="task-file-info">
                            <i data-lucide="${task.status === 'COMPLETED' ? 'check-circle' : 'file-text'}"></i>
                            <span class="task-filename">${task.filename}</span>
                        </div>
                        <span class="task-stage-badge ${stageClass}">${task.status.replace('_', ' ')}</span>
                    </div>

                    <div class="task-progress-bar-wrapper">
                        <div class="task-progress-track">
                            <div class="task-progress-fill" style="width: ${task.progress}%"></div>
                        </div>
                        <div class="task-step-msg">
                            <span>${task.step_message}</span>
                            <span>${task.progress}%</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        if (window.lucide) lucide.createIcons();
    }
}

window.QueueMonitor = QueueMonitor;
