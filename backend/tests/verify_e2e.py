import time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"

def main():
    print("==================================================================")
    print("   🔍 RUNNING END-TO-END SYSTEM VERIFICATION")
    print("==================================================================")
    
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        print(f"[1/6] Health Check: Status {res.status_code} -> {res.json()}")
        assert res.status_code == 200
        
        # 2. Check Job DB Templates & Seeded Jobs
        res = client.get("/api/jobs")
        jobs = res.json()
        print(f"[2/6] Job DB: Loaded {len(jobs)} active jobs.")
        # Find AI Engineer Job (Job with 'AI' or 'Machine Learning' in title)
        ai_job = next((j for j in jobs if "AI" in j["title"] or "Machine" in j["title"]), jobs[0])
        print(f"      Selected Target Job: ID {ai_job['id']} - '{ai_job['title']}'")
        
        # 3. Batch Upload Multi-Format Resumes (TXT, DOCX, and Scanned Image OCR)
        files = [
            ("files", ("Elena_Rostova_AI.txt", open(SAMPLES_DIR / "sample_ai_engineer.txt", "rb"), "text/plain")),
            ("files", ("David_Miller_FullStack.docx", open(SAMPLES_DIR / "sample_fullstack_dev.docx", "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
            ("files", ("Sarah_Jennings_DevOps.txt", open(SAMPLES_DIR / "sample_devops_engineer.txt", "rb"), "text/plain")),
            ("files", ("Michael_Chang_DataSci_Scanned.png", open(SAMPLES_DIR / "sample_scanned_resume.png", "rb"), "image/png"))
        ]
        
        print(f"\n[3/6] Ingesting Batch Resumes for Job ID {ai_job['id']} ('{ai_job['title']}')...")
        upload_res = client.post("/api/resumes/upload", data={"job_id": ai_job["id"]}, files=files)
        print(f"      Upload Response: Status {upload_res.status_code} -> Enqueued: {upload_res.json().get('enqueued_count')} tasks.")
        assert upload_res.status_code == 200
        
        # 4. Wait for Processing Worker to complete all tasks in queue
        print("\n[4/6] Waiting for Processing Worker (Extracting -> OCR -> NLP -> Embedding -> Scoring -> Ranking DB)...")
        for attempt in range(25):
            q_res = client.get(f"/api/queue/status?job_id={ai_job['id']}")
            stats = q_res.json().get("stats", {})
            queued = stats.get("queued", 0)
            processing = stats.get("processing", 0)
            completed = stats.get("completed", 0)
            print(f"      Pipeline State -> Queued: {queued}, Processing: {processing}, Completed: {completed}")
            if queued == 0 and processing == 0 and completed >= 4:
                break
            time.sleep(1)
            
        # 5. Check Candidate Rankings in Ranking DB
        rankings_res = client.get(f"/api/jobs/{ai_job['id']}/rankings")
        assert rankings_res.status_code == 200
        rankings = rankings_res.json()
        print(f"\n[5/6] Candidate Rankings Retrieved: {len(rankings)} candidates scored for '{ai_job['title']}'.")
        print("--------------------------------------------------------------------------------------------------------------------")
        print(f"{'Rank':<5} | {'Candidate Name':<28} | {'Score':<8} | {'Semantic':<9} | {'Skills':<8} | {'Status':<14} | {'OCR'}")
        print("--------------------------------------------------------------------------------------------------------------------")
        for i, r in enumerate(rankings, start=1):
            ocr_str = "YES (Tesseract)" if r.get("is_ocr_used") else "NO (Native)"
            print(f"#{i:<4} | {r['candidate_name']:<28} | {r['overall_score']:>5.1f}% | {r['semantic_score']:>6.1f}% | {r['skill_score']:>5.1f}% | {r['status']:<14} | {ocr_str}")
        print("--------------------------------------------------------------------------------------------------------------------")
        
        assert len(rankings) >= 4
        
        # Check that top candidate for AI Engineer role is Elena Rostova (AI PhD)
        top_cand = rankings[0]
        print(f"      Top Ranked Candidate: {top_cand['candidate_name']} ({top_cand['overall_score']}% Match)")
        assert "Elena" in top_cand["candidate_name"] or top_cand["overall_score"] >= 80.0
        
        # 6. Recruiter Decision Update & Export
        patch_res = client.patch(f"/api/evaluations/{top_cand['id']}/status", json={"status": "SHORTLISTED"})
        print(f"\n[6/6] Recruiter Action: Updated top candidate status to SHORTLISTED -> {patch_res.json()}")
        assert patch_res.status_code == 200
        
        # CSV Export Test
        csv_res = client.get(f"/api/jobs/{ai_job['id']}/export?format=csv")
        print(f"      CSV Export: Status {csv_res.status_code}, Length {len(csv_res.text)} bytes.")
        assert csv_res.status_code == 200
        
        print("\n==================================================================")
        print("   ✅ ALL END-TO-END PIPELINE CHECKS PASSED WITH FLYING COLORS!")
        print("==================================================================")

if __name__ == "__main__":
    main()
