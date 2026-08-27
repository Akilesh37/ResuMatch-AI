/**
 * API Service Client for ResuMatch AI Backend
 */
const getBaseUrl = () => {
    // If opened via file:// protocol or different frontend port (e.g. Live Server), target backend on 8000
    if (typeof window !== 'undefined') {
        if (window.location.protocol === 'file:' || (window.location.port && window.location.port !== '8000')) {
            return 'http://127.0.0.1:8000';
        }
    }
    return '';
};

const API = {
    baseUrl: getBaseUrl(),

    // Helper fetch with clear network error messaging
    async request(url, options = {}) {
        try {
            const res = await fetch(`${this.baseUrl}${url}`, options);
            return res;
        } catch (e) {
            if (e.message === 'Failed to fetch' || e.name === 'TypeError') {
                throw new Error('Backend server is offline or unreachable. Please run ./start.sh or ensure http://127.0.0.1:8000 is active.');
            }
            throw e;
        }
    },

    // Job DB Endpoints
    async getJobs() {
        const res = await this.request('/api/jobs');
        if (!res.ok) throw new Error('Failed to fetch jobs');
        return await res.json();
    },

    async getJobTemplates() {
        const res = await this.request('/api/jobs/templates');
        if (!res.ok) throw new Error('Failed to fetch job templates');
        return await res.json();
    },

    async getJob(jobId) {
        const res = await this.request(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch job details');
        return await res.json();
    },

    async createJob(jobData) {
        const res = await this.request('/api/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Failed to create job' }));
            throw new Error(err.detail || 'Failed to create job');
        }
        return await res.json();
    },

    async deleteJob(jobId) {
        const res = await this.request(`/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete job');
        return await res.json();
    },

    // Resume Ingestion Endpoint
    async uploadResumes(jobId, files) {
        const formData = new FormData();
        formData.append('job_id', jobId);
        for (const file of files) {
            formData.append('files', file);
        }

        const res = await this.request('/api/resumes/upload', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: `Upload failed (Status ${res.status})` }));
            throw new Error(err.detail || 'Upload failed');
        }
        return await res.json();
    },

    // Ranking DB & Results Endpoints
    async getRankings(jobId, filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.minScore) params.append('min_score', filters.minScore);

        const url = `/api/jobs/${jobId}/rankings?${params.toString()}`;
        const res = await this.request(url);
        if (!res.ok) throw new Error('Failed to fetch rankings');
        return await res.json();
    },

    async getCandidate(candidateId) {
        const res = await this.request(`/api/candidates/${candidateId}`);
        if (!res.ok) throw new Error('Failed to fetch candidate details');
        return await res.json();
    },

    async updateEvaluationStatus(evalId, status) {
        const res = await this.request(`/api/evaluations/${evalId}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        if (!res.ok) throw new Error('Failed to update status');
        return await res.json();
    },

    exportRankingsUrl(jobId, format = 'csv') {
        const base = this.baseUrl || '';
        return `${base}/api/jobs/${jobId}/export?format=${format}`;
    },

    // Queue Status & SSE Stream
    async getQueueStatus(jobId = null) {
        const url = jobId ? `/api/queue/status?job_id=${jobId}` : '/api/queue/status';
        const res = await this.request(url);
        if (!res.ok) throw new Error('Failed to fetch queue status');
        return await res.json();
    },

    subscribeQueueStream(onMessage, onError) {
        const sseUrl = `${this.baseUrl}/api/queue/stream`;
        const eventSource = new EventSource(sseUrl);
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                console.error('Error parsing SSE event data', e);
            }
        };
        eventSource.onerror = (err) => {
            if (onError) onError(err);
        };
        return eventSource;
    }
};

window.API = API;
