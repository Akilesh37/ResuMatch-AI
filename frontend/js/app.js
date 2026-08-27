/**
 * Main Application Orchestrator for ResuMatch AI
 */
class App {
    constructor() {
        this.activeTab = 'rankings-tab';
        this.activeJob = null;

        // Initialize Subcomponents
        this.jobManager = new JobManager(this);
        this.uploader = new ResumeUploader(this);
        this.queueMonitor = new QueueMonitor(this);
        this.rankingBoard = new RankingBoard(this);
        this.candidateModal = new CandidateModal(this);

        this.initNavigation();
        this.init();
    }

    async init() {
        if (window.lucide) lucide.createIcons();
        await this.jobManager.init();
    }

    initNavigation() {
        const navButtons = document.querySelectorAll('.nav-item');
        navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                this.switchTab(targetTab);
            });
        });

        // Quick upload header button
        const quickUploadBtn = document.getElementById('btn-quick-upload');
        if (quickUploadBtn) {
            quickUploadBtn.addEventListener('click', () => {
                this.switchTab('upload-tab');
            });
        }
    }

    switchTab(tabId) {
        this.activeTab = tabId;

        // Update nav items
        document.querySelectorAll('.nav-item').forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update tab panes
        document.querySelectorAll('.tab-content').forEach(pane => {
            if (pane.id === tabId) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        // Update Header Title
        const pageTitle = document.getElementById('current-page-title');
        if (pageTitle) {
            switch(tabId) {
                case 'rankings-tab':
                    pageTitle.textContent = 'Candidate Leaderboard';
                    break;
                case 'upload-tab':
                    pageTitle.textContent = 'Batch Resume Ingestion';
                    break;
                case 'queue-tab':
                    pageTitle.textContent = 'Live Processing Queue';
                    break;
                case 'jobs-tab':
                    pageTitle.textContent = 'Job DB & Criteria';
                    break;
            }
        }

        if (window.lucide) lucide.createIcons();
    }

    onActiveJobChanged(job) {
        this.activeJob = job;
        const jobSubtitle = document.getElementById('current-job-subtitle');
        if (jobSubtitle) {
            jobSubtitle.textContent = `Screening candidates for: ${job.title} (${job.department || 'General'})`;
        }
        this.rankingBoard.setActiveJob(job);
    }

    onTaskCompleted(task) {
        // If the task belongs to the active job, reload leaderboard
        if (this.activeJob && task.job_id === this.activeJob.id) {
            this.rankingBoard.loadRankings(this.activeJob.id);
            this.showToast(`New candidate evaluated: ${task.filename}`, 'success');
        }
    }

    getActiveJobId() {
        return this.activeJob ? this.activeJob.id : null;
    }

    openCandidateModal(candidateId, evalId) {
        this.candidateModal.open(candidateId, evalId);
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        let iconName = 'info';
        if (type === 'success') iconName = 'check-circle';
        if (type === 'warning') iconName = 'alert-triangle';
        if (type === 'danger') iconName = 'alert-circle';

        toast.innerHTML = `
            <i data-lucide="${iconName}"></i>
            <span>${message}</span>
        `;
        container.appendChild(toast);
        if (window.lucide) lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
    window.jobManager = window.app.jobManager;
    window.uploader = window.app.uploader;
    window.rankingBoard = window.app.rankingBoard;
});
