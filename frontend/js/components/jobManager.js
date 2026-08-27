/**
 * Job Manager Component - Handles Job DB operations and criteria configuration
 */
class JobManager {
    constructor(app) {
        this.app = app;
        this.templates = [];
        this.jobs = [];
        this.activeJobId = null;

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.globalSelect = document.getElementById('global-job-select');
        this.templateSelect = document.getElementById('template-select');
        this.jobForm = document.getElementById('job-form');
        this.savedJobsList = document.getElementById('saved-jobs-list');

        // Form Fields
        this.titleInput = document.getElementById('job-title-input');
        this.deptInput = document.getElementById('job-dept-input');
        this.descInput = document.getElementById('job-desc-input');
        this.reqSkillsInput = document.getElementById('job-req-skills-input');
        this.prefSkillsInput = document.getElementById('job-pref-skills-input');
        this.expInput = document.getElementById('job-exp-input');
        this.thresholdInput = document.getElementById('job-threshold-input');

        // Weight Sliders
        this.sliderSemantic = document.getElementById('slider-weight-semantic');
        this.sliderSkills = document.getElementById('slider-weight-skills');
        this.sliderExp = document.getElementById('slider-weight-experience');
        this.sliderKw = document.getElementById('slider-weight-keywords');

        this.labelSemantic = document.getElementById('label-weight-semantic');
        this.labelSkills = document.getElementById('label-weight-skills');
        this.labelExp = document.getElementById('label-weight-experience');
        this.labelKw = document.getElementById('label-weight-keywords');
        this.weightsSumBadge = document.getElementById('weights-sum-badge');
    }

    bindEvents() {
        // Global Job Selector Change
        this.globalSelect.addEventListener('change', (e) => {
            const jobId = parseInt(e.target.value);
            this.setActiveJob(jobId);
        });

        // Template Selector Change
        this.templateSelect.addEventListener('change', (e) => {
            const idx = parseInt(e.target.value);
            if (!isNaN(idx) && this.templates[idx]) {
                this.loadTemplateIntoForm(this.templates[idx]);
            }
        });

        // Weight Sliders Input Events
        const sliders = [this.sliderSemantic, this.sliderSkills, this.sliderExp, this.sliderKw];
        sliders.forEach(slider => {
            slider.addEventListener('input', () => this.updateWeightLabels());
        });

        // Form Submit
        this.jobForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }

    async init() {
        await Promise.all([
            this.loadTemplates(),
            this.loadJobs()
        ]);
    }

    async loadTemplates() {
        try {
            this.templates = await API.getJobTemplates();
            this.templateSelect.innerHTML = '<option value="" disabled selected>Choose a template...</option>' +
                this.templates.map((t, i) => `<option value="${i}">${t.title}</option>`).join('');
        } catch (e) {
            console.error('Failed to load templates', e);
        }
    }

    async loadJobs() {
        try {
            this.jobs = await API.getJobs();
            this.renderGlobalSelect();
            this.renderSavedJobsList();

            if (this.jobs.length > 0 && !this.activeJobId) {
                this.setActiveJob(this.jobs[0].id);
            }
        } catch (e) {
            this.app.showToast('Failed to load jobs from Job DB', 'danger');
        }
    }

    renderGlobalSelect() {
        if (this.jobs.length === 0) {
            this.globalSelect.innerHTML = '<option value="" disabled selected>No Jobs Configured</option>';
            return;
        }

        this.globalSelect.innerHTML = this.jobs.map(j => 
            `<option value="${j.id}" ${j.id === this.activeJobId ? 'selected' : ''}>${j.title} (${j.department || 'General'})</option>`
        ).join('');
    }

    renderSavedJobsList() {
        if (this.jobs.length === 0) {
            this.savedJobsList.innerHTML = '<p class="text-muted text-center py-4">No jobs in database yet.</p>';
            return;
        }

        this.savedJobsList.innerHTML = this.jobs.map(j => `
            <div class="saved-job-card ${j.id === this.activeJobId ? 'active' : ''}" onclick="jobManager.setActiveJob(${j.id})">
                <div class="saved-job-title">${j.title}</div>
                <div class="saved-job-meta">
                    <span>${j.department || 'General'}</span> • 
                    <span>Min ${j.min_experience} yrs</span> • 
                    <span>${j.total_candidates} evaluated</span>
                </div>
            </div>
        `).join('');
    }

    setActiveJob(jobId) {
        this.activeJobId = jobId;
        const job = this.jobs.find(j => j.id === jobId);
        if (job) {
            this.globalSelect.value = jobId;
            this.renderSavedJobsList();
            this.app.onActiveJobChanged(job);
        }
    }

    loadTemplateIntoForm(tmpl) {
        this.titleInput.value = tmpl.title;
        this.deptInput.value = tmpl.department;
        this.descInput.value = tmpl.description;
        this.reqSkillsInput.value = tmpl.required_skills.join(', ');
        this.prefSkillsInput.value = tmpl.preferred_skills.join(', ');
        this.expInput.value = tmpl.min_experience;
        this.thresholdInput.value = tmpl.threshold;

        this.sliderSemantic.value = Math.round(tmpl.weight_semantic * 100);
        this.sliderSkills.value = Math.round(tmpl.weight_skills * 100);
        this.sliderExp.value = Math.round(tmpl.weight_experience * 100);
        this.sliderKw.value = Math.round(tmpl.weight_keywords * 100);

        this.updateWeightLabels();
        this.app.showToast(`Loaded template: ${tmpl.title}`, 'info');
    }

    updateWeightLabels() {
        const sem = parseInt(this.sliderSemantic.value) || 0;
        const skl = parseInt(this.sliderSkills.value) || 0;
        const exp = parseInt(this.sliderExp.value) || 0;
        const kw = parseInt(this.sliderKw.value) || 0;

        this.labelSemantic.textContent = `${sem}%`;
        this.labelSkills.textContent = `${skl}%`;
        this.labelExp.textContent = `${exp}%`;
        this.labelKw.textContent = `${kw}%`;

        const total = sem + skl + exp + kw;
        this.weightsSumBadge.textContent = `Total: ${total}%`;
        if (total === 100) {
            this.weightsSumBadge.style.color = 'var(--success)';
            this.weightsSumBadge.style.borderColor = 'var(--success-border)';
        } else {
            this.weightsSumBadge.style.color = 'var(--warning)';
            this.weightsSumBadge.style.borderColor = 'var(--warning-border)';
        }
    }

    async handleFormSubmit(e) {
        e.preventDefault();

        const reqSkills = this.reqSkillsInput.value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
        const prefSkills = this.prefSkillsInput.value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);

        const sem = parseInt(this.sliderSemantic.value) / 100.0;
        const skl = parseInt(this.sliderSkills.value) / 100.0;
        const exp = parseInt(this.sliderExp.value) / 100.0;
        const kw = parseInt(this.sliderKw.value) / 100.0;

        const payload = {
            title: this.titleInput.value.trim(),
            department: this.deptInput.value.trim() || 'General',
            description: this.descInput.value.trim(),
            required_skills: reqSkills,
            preferred_skills: prefSkills,
            min_experience: parseFloat(this.expInput.value) || 0.0,
            threshold: parseFloat(this.thresholdInput.value) || 50.0,
            weight_semantic: sem,
            weight_skills: skl,
            weight_experience: exp,
            weight_keywords: kw
        };

        try {
            const newJob = await API.createJob(payload);
            this.app.showToast(`Job '${newJob.title}' created and activated in Job DB!`, 'success');
            await this.loadJobs();
            this.setActiveJob(newJob.id);
            this.app.switchTab('rankings-tab');
        } catch (err) {
            this.app.showToast(err.message, 'danger');
        }
    }
}

window.JobManager = JobManager;
