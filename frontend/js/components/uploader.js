/**
 * Uploader Component - Handles Drag-and-Drop, staging, sample synthesis, and batch ingestion
 */
class ResumeUploader {
    constructor(app) {
        this.app = app;
        this.stagedFiles = [];

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.dropzone = document.getElementById('resume-dropzone');
        this.fileInput = document.getElementById('file-input');
        this.browseBtn = document.getElementById('btn-browse-files');
        this.stagedContainer = document.getElementById('staged-files-container');
        this.stagedList = document.getElementById('staged-list');
        this.stagedCount = document.getElementById('staged-count');
        this.clearBtn = document.getElementById('btn-clear-staged');
        this.submitBtn = document.getElementById('btn-submit-upload');

        // Sample Quick Test Buttons
        this.sampleAiBtn = document.getElementById('btn-load-sample-ai');
        this.sampleFsBtn = document.getElementById('btn-load-sample-fullstack');
        this.sampleOcrBtn = document.getElementById('btn-load-sample-ocr');
    }

    bindEvents() {
        // Dropzone interactions
        this.dropzone.addEventListener('click', (e) => {
            if (e.target !== this.browseBtn) {
                this.fileInput.click();
            }
        });

        this.browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });

        this.fileInput.addEventListener('change', (e) => {
            this.handleFilesAdded(Array.from(e.target.files));
            this.fileInput.value = '';
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropzone.classList.remove('dragover');
            });
        });

        this.dropzone.addEventListener('drop', (e) => {
            const files = Array.from(e.dataTransfer.files);
            this.handleFilesAdded(files);
        });

        this.clearBtn.addEventListener('click', () => this.clearStaged());
        this.submitBtn.addEventListener('click', () => this.submitBatchUpload());

        // Sample Loaders
        this.sampleAiBtn.addEventListener('click', () => this.loadSampleResume('ai'));
        this.sampleFsBtn.addEventListener('click', () => this.loadSampleResume('fullstack'));
        this.sampleOcrBtn.addEventListener('click', () => this.loadSampleResume('ocr'));
    }

    handleFilesAdded(newFiles) {
        if (!newFiles || newFiles.length === 0) return;

        for (const file of newFiles) {
            // Avoid duplicate filenames in staged
            if (!this.stagedFiles.some(f => f.name === file.name)) {
                this.stagedFiles.push(file);
            }
        }

        this.renderStagedList();
        this.app.showToast(`Added ${newFiles.length} file(s) to staging`, 'info');
    }

    removeStagedFile(index) {
        this.stagedFiles.splice(index, 1);
        this.renderStagedList();
    }

    clearStaged() {
        this.stagedFiles = [];
        this.renderStagedList();
    }

    renderStagedList() {
        if (this.stagedFiles.length === 0) {
            this.stagedContainer.style.display = 'none';
            return;
        }

        this.stagedContainer.style.display = 'block';
        this.stagedCount.textContent = this.stagedFiles.length;

        this.stagedList.innerHTML = this.stagedFiles.map((file, idx) => {
            const sizeKb = (file.size / 1024).toFixed(1);
            return `
                <li class="staged-item">
                    <div class="staged-item-info">
                        <i data-lucide="file-text"></i>
                        <div>
                            <strong>${file.name}</strong>
                            <span class="staged-size">(${sizeKb} KB)</span>
                        </div>
                    </div>
                    <button class="btn-icon" onclick="uploader.removeStagedFile(${idx})" title="Remove file">
                        <i data-lucide="trash-2"></i>
                    </button>
                </li>
            `;
        }).join('');

        if (window.lucide) lucide.createIcons();
    }

    async submitBatchUpload() {
        const jobId = this.app.getActiveJobId();
        if (!jobId) {
            this.app.showToast('Please select or create an active job first!', 'warning');
            return;
        }

        if (this.stagedFiles.length === 0) {
            this.app.showToast('No resumes staged for upload!', 'warning');
            return;
        }

        this.submitBtn.disabled = true;
        this.submitBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Enqueueing Resumes...';
        if (window.lucide) lucide.createIcons();

        try {
            const res = await API.uploadResumes(jobId, this.stagedFiles);
            this.app.showToast(res.message, 'success');
            this.clearStaged();
            // Redirect to Queue Monitor tab to watch live progress
            this.app.switchTab('queue-tab');
        } catch (err) {
            this.app.showToast(`Upload failed: ${err.message}`, 'danger');
        } finally {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = '<i data-lucide="play"></i> <span>Enqueue & Start Processing Pipeline</span>';
            if (window.lucide) lucide.createIcons();
        }
    }

    loadSampleResume(type) {
        let sampleText = '';
        let filename = '';

        if (type === 'ai') {
            filename = 'Alex_Vance_Senior_AI_Engineer.txt';
            sampleText = `ALEX VANCE
Email: alex.vance.ai@gmail.com | Phone: +1-415-555-0192 | San Francisco, CA

PROFESSIONAL SUMMARY
Passionate Senior AI/ML Engineer with 4.5 years of experience architecting large language model pipelines, transformer embeddings, and deep learning systems using PyTorch and HuggingFace.

WORK EXPERIENCE
Senior Machine Learning Engineer | NeuroScale AI (2021 - Present)
- Developed transformer-based semantic search and RAG retrieval pipelines using PyTorch and FastAPI, reducing query latency by 45%.
- Implemented and fine-tuned BERT and LLM models for entity recognition and candidate matching.
- Orchestrated containerized model inference with Docker and Kubernetes on AWS.

Machine Learning Developer | Apex Data Labs (2019 - 2021)
- Built predictive models and classification engines using Scikit-Learn, Pandas, and XGBoost.
- Designed automated CI/CD deployment pipelines for machine learning models.

SKILLS
Python, PyTorch, Transformers, Deep Learning, Machine Learning, LLMs, LangChain, Vector Databases, FastAPI, Docker, Kubernetes, AWS, SQL, Scikit-Learn, Git.

EDUCATION
B.Tech in Computer Science & Engineering | University of California, Berkeley (2019)`;
        } else if (type === 'fullstack') {
            filename = 'Sophia_Chen_FullStack_Engineer.txt';
            sampleText = `SOPHIA CHEN
Email: sophia.chen.dev@outlook.com | Phone: +1-206-555-8391 | Seattle, WA

SUMMARY
Full Stack Engineer with 3.5 years of experience building high-performance web applications and distributed backend systems with React, TypeScript, Node.js, Python, and PostgreSQL.

EXPERIENCE
Full Stack Developer | CloudCraft Solutions (2022 - Present)
- Architected enterprise dashboards using React, TypeScript, Next.js, and Tailwind CSS.
- Developed scalable REST APIs and microservices using Node.js, Express, and PostgreSQL.
- Implemented in-memory caching with Redis and containerized microservices via Docker.

Software Engineer | WebPulse Interactive (2020 - 2022)
- Built interactive UI components and integrated GraphQL / REST endpoints.
- Collaborated in agile team sprints with continuous CI/CD deployments.

CORE COMPETENCIES
JavaScript, TypeScript, React, Next.js, Node.js, Express, Python, PostgreSQL, REST API, Redis, Docker, Tailwind CSS, Git, Agile.

EDUCATION
Bachelor of Science in Software Engineering | University of Washington (2020)`;
        } else if (type === 'ocr') {
            // Scanned text simulating OCR capture
            filename = 'Marcus_Reynolds_CloudDevOps_Scanned.txt';
            sampleText = `MARCUS REYNOLDS
Cloud & DevOps Infrastructure Specialist
Email: marcus.reynolds@cloudinfra.io | Phone: +1-512-555-7721

EXPERIENCE:
Lead Cloud DevOps Engineer | SkyScale Systems (2020 - Present)
- Designed and maintained multi-region Kubernetes clusters across AWS and GCP.
- Automated complete Infrastructure-as-Code using Terraform and Ansible.
- Built automated CI/CD pipelines with GitHub Actions and Docker.
- Implemented Linux system security and automated backup recovery.

DevOps Engineer | ByteMatrix Technologies (2018 - 2020)
- Managed Linux server configurations and Nginx reverse proxies.
- Automated bash scripting for system monitoring and log aggregation.

SKILLS:
Docker, Kubernetes, AWS, Terraform, CI/CD, Linux, Bash, Git, Ansible, GCP, Python, Nginx, Security.

EDUCATION:
B.S. in Information Technology (2018)`;
        }

        const blob = new Blob([sampleText], { type: 'text/plain' });
        const file = new File([blob], filename, { type: 'text/plain' });
        this.handleFilesAdded([file]);
    }
}

window.ResumeUploader = ResumeUploader;
