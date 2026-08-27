/**
 * Candidate Leaderboard & Ranking Board Component
 */
class RankingBoard {
    constructor(app) {
        this.app = app;
        this.rankings = [];
        this.activeJob = null;

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.tableBody = document.getElementById('rankings-table-body');
        this.searchInput = document.getElementById('candidate-search-input');
        this.statusFilter = document.getElementById('filter-status');
        this.minScoreFilter = document.getElementById('filter-min-score');
        this.exportBtn = document.getElementById('btn-export-csv');
        this.refreshBtn = document.getElementById('btn-refresh-rankings');
        this.jobStrip = document.getElementById('active-job-strip');

        // Header statistics
        this.statTotal = document.getElementById('stat-total-candidates');
        this.statShortlisted = document.getElementById('stat-shortlisted');
        this.navCountBadge = document.getElementById('nav-count-badge');
    }

    bindEvents() {
        this.searchInput.addEventListener('input', () => this.render());
        this.statusFilter.addEventListener('change', () => this.render());
        this.minScoreFilter.addEventListener('change', () => this.render());

        this.refreshBtn.addEventListener('click', () => {
            if (this.activeJob) {
                this.loadRankings(this.activeJob.id);
                this.app.showToast('Leaderboard refreshed', 'info');
            }
        });

        this.exportBtn.addEventListener('click', () => {
            if (!this.activeJob) {
                this.app.showToast('No active job selected', 'warning');
                return;
            }
            window.location.href = API.exportRankingsUrl(this.activeJob.id, 'csv');
        });
    }

    setActiveJob(job) {
        this.activeJob = job;
        this.renderJobSummaryStrip();
        this.loadRankings(job.id);
    }

    renderJobSummaryStrip() {
        if (!this.activeJob) {
            this.jobStrip.style.display = 'none';
            return;
        }

        this.jobStrip.style.display = 'flex';
        const reqList = this.activeJob.required_skills || [];
        const chipsHtml = reqList.slice(0, 6).map(s => `<span class="skill-tag">${s}</span>`).join('');

        this.jobStrip.innerHTML = `
            <div class="strip-info">
                <h4>🎯 Screening Criteria: ${this.activeJob.title} (${this.activeJob.department || 'General'})</h4>
                <p>Min Experience: <strong>${this.activeJob.min_experience} yrs</strong> | Pass Threshold: <strong>${this.activeJob.threshold}%</strong></p>
            </div>
            <div class="strip-tags">
                <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">Key Requirements:</span>
                ${chipsHtml}
                ${reqList.length > 6 ? `<span class="skill-tag">+${reqList.length - 6} more</span>` : ''}
            </div>
        `;
    }

    async loadRankings(jobId) {
        try {
            this.rankings = await API.getRankings(jobId);
            this.updateHeaderStats();
            this.render();
        } catch (e) {
            console.error('Failed to load rankings', e);
        }
    }

    updateHeaderStats() {
        const total = this.rankings.length;
        const shortlisted = this.rankings.filter(r => r.status === 'SHORTLISTED').length;

        if (this.statTotal) this.statTotal.textContent = `${total} Candidates`;
        if (this.statShortlisted) this.statShortlisted.textContent = `${shortlisted} Shortlisted`;
        if (this.navCountBadge) this.navCountBadge.textContent = total;
    }

    getFilteredRankings() {
        const query = this.searchInput.value.toLowerCase().trim();
        const status = this.statusFilter.value;
        const minScore = parseFloat(this.minScoreFilter.value) || 0;

        return this.rankings.filter(r => {
            const matchesQuery = !query || 
                r.candidate_name.toLowerCase().includes(query) ||
                (r.candidate_email && r.candidate_email.toLowerCase().includes(query)) ||
                r.matched_skills.some(s => s.toLowerCase().includes(query));

            const matchesStatus = !status || r.status === status;
            const matchesScore = r.overall_score >= minScore;

            return matchesQuery && matchesStatus && matchesScore;
        });
    }

    render() {
        const filtered = this.getFilteredRankings();

        if (filtered.length === 0) {
            this.tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state-cell">
                        <div class="empty-state">
                            <i data-lucide="users"></i>
                            <h3>No Candidates Match Filter</h3>
                            <p>Try clearing your search query or adjusting status / score filters.</p>
                        </div>
                    </td>
                </tr>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        this.tableBody.innerHTML = filtered.map((item, idx) => {
            const rank = idx + 1;
            const rankClass = rank <= 3 ? `rank-${rank}` : '';
            
            const scoreClass = item.overall_score >= 75 ? 'score-high' :
                               item.overall_score >= 50 ? 'score-med' : 'score-low';

            const statusClass = `status-${item.status.toLowerCase()}`;

            const skillsHtml = item.matched_skills.slice(0, 4).map(s => 
                `<span class="skill-tag">${s}</span>`
            ).join('') + (item.matched_skills.length > 4 ? `<span class="skill-tag">+${item.matched_skills.length - 4}</span>` : '');

            return `
                <tr>
                    <td class="col-rank">
                        <span class="rank-badge ${rankClass}">${rank}</span>
                    </td>
                    <td class="col-candidate">
                        <div class="candidate-profile-cell">
                            <span class="candidate-name">${item.candidate_name}</span>
                            <div class="candidate-sub">
                                <span>${item.candidate_experience > 0 ? `${item.candidate_experience} yrs exp` : 'Entry / Unspecified'}</span>
                                ${item.is_ocr_used ? `<span class="badge-ocr"><i data-lucide="scan"></i> OCR</span>` : ''}
                            </div>
                        </div>
                    </td>
                    <td class="col-score">
                        <div class="score-display ${scoreClass}">
                            <span class="score-number">${Math.round(item.overall_score)}</span>
                            <span class="score-unit">%</span>
                        </div>
                    </td>
                    <td class="col-breakdown">
                        <div class="breakdown-bars">
                            <div class="mini-bar-item">
                                <span>Semantic:</span>
                                <div class="mini-progress-track">
                                    <div class="mini-progress-fill fill-semantic" style="width: ${item.semantic_score}%"></div>
                                </div>
                            </div>
                            <div class="mini-bar-item">
                                <span>Skills:</span>
                                <div class="mini-progress-track">
                                    <div class="mini-progress-fill fill-skills" style="width: ${item.skill_score}%"></div>
                                </div>
                            </div>
                            <div class="mini-bar-item">
                                <span>Experience:</span>
                                <div class="mini-progress-track">
                                    <div class="mini-progress-fill fill-exp" style="width: ${item.experience_score}%"></div>
                                </div>
                            </div>
                        </div>
                    </td>
                    <td class="col-skills">
                        <div class="strip-tags">
                            ${skillsHtml || '<span style="color:var(--text-muted);font-size:0.75rem;">None</span>'}
                        </div>
                    </td>
                    <td class="col-status">
                        <span class="status-pill ${statusClass}">
                            ${item.status.replace('_', ' ')}
                        </span>
                    </td>
                    <td class="col-actions">
                        <button class="btn btn-sm btn-secondary" onclick="app.openCandidateModal(${item.candidate_id}, ${item.id})" title="Inspect Candidate & OCR text">
                            <i data-lucide="eye"></i>
                            <span>Details</span>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        if (window.lucide) lucide.createIcons();
    }
}

window.RankingBoard = RankingBoard;
