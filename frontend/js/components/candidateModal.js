/**
 * Candidate Modal Component - Deep-dive OCR text inspector, score radar, and recruiter actions
 */
class CandidateModal {
    constructor(app) {
        this.app = app;
        this.currentEvalId = null;
        this.currentCandidateId = null;

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.backdrop = document.getElementById('candidate-modal-backdrop');
        this.closeBtn = document.getElementById('btn-close-modal');

        // Header elements
        this.modalName = document.getElementById('modal-candidate-name');
        this.modalBadges = document.getElementById('modal-candidate-badges');

        // Metrics elements
        this.scoreOverall = document.getElementById('modal-score-overall');
        this.scoreStatus = document.getElementById('modal-score-status');
        this.scoreSemantic = document.getElementById('modal-score-semantic');
        this.scoreSkills = document.getElementById('modal-score-skills');
        this.skillsCount = document.getElementById('modal-skills-count');
        this.scoreExp = document.getElementById('modal-score-exp');
        this.candYears = document.getElementById('modal-candidate-years');

        // AI Summary & Strengths
        this.aiSummary = document.getElementById('modal-ai-summary');
        this.strengthsList = document.getElementById('modal-strengths-list');
        this.gapsList = document.getElementById('modal-gaps-list');

        // Meta elements
        this.candEmail = document.getElementById('modal-candidate-email');
        this.candPhone = document.getElementById('modal-candidate-phone');
        this.candFile = document.getElementById('modal-candidate-file');
        this.candOcrStatus = document.getElementById('modal-candidate-ocr-status');

        // Skills Chips
        this.matchedChips = document.getElementById('modal-matched-chips');
        this.missingChips = document.getElementById('modal-missing-chips');
        this.extraChips = document.getElementById('modal-extra-chips');

        // OCR Raw Text Inspector
        this.ocrTag = document.getElementById('modal-ocr-tag');
        this.rawTextContent = document.getElementById('modal-raw-text-content');
        this.copyTextBtn = document.getElementById('btn-copy-raw-text');

        // Modal Tab Buttons
        this.tabBtns = document.querySelectorAll('.modal-tab-btn');
        this.tabPanes = document.querySelectorAll('.modal-tab-pane');

        // Recruiter Actions
        this.btnShortlist = document.getElementById('btn-action-shortlist');
        this.btnReview = document.getElementById('btn-action-review');
        this.btnReject = document.getElementById('btn-action-reject');
    }

    bindEvents() {
        this.closeBtn.addEventListener('click', () => this.close());
        this.backdrop.addEventListener('click', (e) => {
            if (e.target === this.backdrop) this.close();
        });

        // Tab Switching inside Modal
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-modal-tab');
                this.tabBtns.forEach(b => b.classList.remove('active'));
                this.tabPanes.forEach(p => p.classList.remove('active'));

                btn.classList.add('active');
                const targetPane = document.getElementById(targetId);
                if (targetPane) targetPane.classList.add('active');
            });
        });

        // Copy Raw Text
        this.copyTextBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(this.rawTextContent.textContent);
            this.app.showToast('Copied extracted resume text to clipboard!', 'info');
        });

        // Recruiter Actions
        this.btnShortlist.addEventListener('click', () => this.updateStatus('SHORTLISTED'));
        this.btnReview.addEventListener('click', () => this.updateStatus('UNDER_REVIEW'));
        this.btnReject.addEventListener('click', () => this.updateStatus('REJECTED'));
    }

    async open(candidateId, evalId) {
        this.currentCandidateId = candidateId;
        this.currentEvalId = evalId;
        this.backdrop.style.display = 'flex';

        // Reset to first tab
        this.tabBtns[0].click();

        try {
            // Fetch both candidate and evaluation records
            const candidate = await API.getCandidate(candidateId);
            const rankings = this.app.rankingBoard.rankings;
            const evaluation = rankings.find(r => r.id === evalId);

            if (candidate && evaluation) {
                this.populateData(candidate, evaluation);
            }
        } catch (e) {
            this.app.showToast('Failed to load candidate details', 'danger');
            this.close();
        }
    }

    populateData(candidate, evaluation) {
        // Name and Badges
        this.modalName.textContent = candidate.name;
        this.modalBadges.innerHTML = `
            <span class="status-pill status-${evaluation.status.toLowerCase()}">${evaluation.status.replace('_', ' ')}</span>
            ${candidate.is_ocr_used ? `<span class="badge-ocr"><i data-lucide="scan"></i> OCR Scanned Document</span>` : ''}
        `;

        // Metric Values
        this.scoreOverall.textContent = `${Math.round(evaluation.overall_score)}%`;
        this.scoreStatus.textContent = evaluation.status.replace('_', ' ');

        this.scoreSemantic.textContent = `${Math.round(evaluation.semantic_score)}%`;
        this.scoreSkills.textContent = `${Math.round(evaluation.skill_score)}%`;
        this.skillsCount.textContent = `${evaluation.matched_skills.length} Matched`;

        this.scoreExp.textContent = `${Math.round(evaluation.experience_score)}%`;
        this.candYears.textContent = `${candidate.total_experience_years} Years`;

        // AI Assessment
        const expl = evaluation.explanation || {};
        this.aiSummary.textContent = expl.summary || 'Candidate analyzed using hybrid semantic and skill matching.';
        
        const strengths = expl.strengths || [];
        this.strengthsList.innerHTML = strengths.map(s => `<li>• ${s}</li>`).join('') || '<li>• General profile alignment</li>';

        const gaps = expl.weaknesses || [];
        this.gapsList.innerHTML = gaps.map(g => `<li>• ${g}</li>`).join('') || '<li>• No significant gaps found</li>';

        // Meta Info
        this.candEmail.textContent = candidate.email || 'Email not detected';
        this.candPhone.textContent = candidate.phone || 'Phone not detected';
        this.candFile.textContent = candidate.original_filename;
        this.candOcrStatus.textContent = candidate.is_ocr_used ? `OCR (Confidence: ${candidate.ocr_confidence || 85}%)` : 'Native PDF/DOCX Parser';

        // Skills Chips
        this.matchedChips.innerHTML = evaluation.matched_skills.map(s => 
            `<span class="chip chip-matched">✓ ${s}</span>`
        ).join('') || '<span class="text-muted">None</span>';

        this.missingChips.innerHTML = evaluation.missing_skills.map(s => 
            `<span class="chip chip-missing">✕ ${s}</span>`
        ).join('') || '<span class="text-success" style="font-size:0.8rem;">All required skills present!</span>';

        const extraList = candidate.extracted_skills.filter(s => !evaluation.matched_skills.includes(s));
        this.extraChips.innerHTML = extraList.map(s => 
            `<span class="chip chip-extra">${s}</span>`
        ).join('') || '<span class="text-muted">None</span>';

        // Raw Text & OCR Inspector
        if (candidate.is_ocr_used) {
            this.ocrTag.innerHTML = `<i data-lucide="sparkles"></i> <span>Tesseract OCR Pipeline (Extracted from Scanned/Image Doc)</span>`;
            this.ocrTag.style.color = 'var(--accent-cyan)';
        } else {
            this.ocrTag.innerHTML = `<i data-lucide="check"></i> <span>Native Text Extraction</span>`;
            this.ocrTag.style.color = 'var(--info)';
        }
        this.rawTextContent.textContent = candidate.raw_text || 'No text extracted.';

        if (window.lucide) lucide.createIcons();
    }

    async updateStatus(newStatus) {
        if (!this.currentEvalId) return;
        try {
            await API.updateEvaluationStatus(this.currentEvalId, newStatus);
            this.app.showToast(`Candidate status marked as ${newStatus}`, 'success');
            // Refresh rankings
            const activeJobId = this.app.getActiveJobId();
            if (activeJobId) {
                await this.app.rankingBoard.loadRankings(activeJobId);
            }
            this.close();
        } catch (e) {
            this.app.showToast('Failed to update candidate status', 'danger');
        }
    }

    close() {
        this.backdrop.style.display = 'none';
        this.currentEvalId = null;
        this.currentCandidateId = null;
    }
}

window.CandidateModal = CandidateModal;
