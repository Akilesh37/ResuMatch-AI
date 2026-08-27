import re
from typing import List, Set, Dict, Tuple

# Comprehensive taxonomy of skills organized by domain with aliases
SKILL_TAXONOMY = {
    # Programming Languages
    "python": ["python", "py", "python3"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java", "j2ee", "core java"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp", ".net"],
    "c": ["c lang", "c programming"],
    "golang": ["go", "golang"],
    "rust": ["rust", "rustlang"],
    "ruby": ["ruby", "ruby on rails", "rails"],
    "php": ["php", "laravel", "symfony"],
    "swift": ["swift", "swiftui"],
    "kotlin": ["kotlin", "android kotlin"],
    "r": ["r lang", "r programming"],
    "scala": ["scala"],
    "sql": ["sql", "tsql", "plsql"],
    "html5": ["html", "html5"],
    "css3": ["css", "css3", "sass", "scss", "less"],
    "bash": ["bash", "shell scripting", "sh", "zsh"],

    # AI / Machine Learning & Data Science
    "machine learning": ["machine learning", "ml", "pattern recognition"],
    "deep learning": ["deep learning", "dl", "neural networks", "ann", "cnn", "rnn", "lstm"],
    "natural language processing": ["natural language processing", "nlp", "ner", "text mining", "spacy", "nltk"],
    "computer vision": ["computer vision", "cv", "opencv", "yolo", "image segmentation"],
    "transformers": ["transformers", "huggingface", "bert", "gpt", "t5", "roberta"],
    "llms": ["llm", "llms", "large language models", "rag", "retrieval augmented generation", "prompt engineering"],
    "langchain": ["langchain", "llamaindex", "langgraph"],
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf", "keras"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scipy": ["scipy"],
    "xgboost": ["xgboost", "lightgbm", "catboost"],
    "data science": ["data science", "predictive modeling", "statistical modeling"],
    "data analysis": ["data analysis", "exploratory data analysis", "eda"],
    "reinforcement learning": ["reinforcement learning", "rl", "q-learning"],
    "generative ai": ["generative ai", "genai", "diffusion models", "stable diffusion"],
    "vector databases": ["vector database", "chromadb", "pinecone", "weaviate", "qdrant", "faiss", "milvus"],

    # Web & Full Stack Frameworks
    "react": ["react", "react.js", "reactjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "angular": ["angular", "angularjs"],
    "next.js": ["next.js", "nextjs", "next"],
    "node.js": ["node", "node.js", "nodejs"],
    "express": ["express", "express.js", "expressjs"],
    "fastapi": ["fastapi", "fast-api"],
    "django": ["django", "django rest framework", "drf"],
    "flask": ["flask"],
    "spring boot": ["spring boot", "spring framework", "spring"],
    "graphql": ["graphql", "apollo"],
    "rest api": ["rest", "restful", "rest api", "rest apis", "restful api", "web api"],
    "tailwind css": ["tailwind", "tailwindcss"],
    "bootstrap": ["bootstrap"],
    "svelte": ["svelte", "sveltekit"],

    # Cloud & DevOps
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda", "rds", "cloudformation", "iam"],
    "azure": ["azure", "microsoft azure", "azure devops"],
    "gcp": ["gcp", "google cloud", "google cloud platform", "bigquery"],
    "docker": ["docker", "containerization", "docker-compose"],
    "kubernetes": ["kubernetes", "k8s", "helm"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment", "github actions", "gitlab ci", "jenkins"],
    "terraform": ["terraform", "iac", "infrastructure as code"],
    "ansible": ["ansible"],
    "linux": ["linux", "ubuntu", "debian", "centos", "redhat", "unix"],
    "microservices": ["microservices", "microservice architecture", "distributed systems"],
    "nginx": ["nginx", "reverse proxy"],

    # Databases & Caching
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql", "mariadb"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis", "in-memory cache", "caching"],
    "elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    "cassandra": ["cassandra"],
    "dynamodb": ["dynamodb"],
    "sqlite": ["sqlite", "sqlite3"],
    "kafka": ["kafka", "apache kafka", "event streaming"],
    "rabbitmq": ["rabbitmq", "message queue", "amqp"],

    # Data Engineering & BI
    "spark": ["spark", "pyspark", "apache spark"],
    "hadoop": ["hadoop", "mapreduce"],
    "airflow": ["airflow", "apache airflow"],
    "dbt": ["dbt", "data build tool"],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "snowflake": ["snowflake"],
    "databricks": ["databricks"],

    # Architecture, Testing & Methodologies
    "git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "agile": ["agile", "scrum", "kanban", "sprint"],
    "test driven development": ["tdd", "test driven development", "unit testing", "pytest", "jest", "cypress", "selenium"],
    "system design": ["system design", "software architecture", "high level design", "low level design", "scalability"],
    "security": ["cybersecurity", "owasp", "oauth", "jwt", "ssl", "tls", "encryption", "auth0"],

    # Soft Skills & Leadership
    "problem solving": ["problem solving", "analytical thinking", "critical thinking"],
    "communication": ["communication", "presentation skills", "written communication"],
    "leadership": ["leadership", "team lead", "mentorship", "project management"],
    "collaboration": ["collaboration", "cross-functional", "team player"]
}

# Reverse lookup dictionary: alias -> canonical skill name
ALIAS_TO_CANONICAL: Dict[str, str] = {}
for canonical, aliases in SKILL_TAXONOMY.items():
    ALIAS_TO_CANONICAL[canonical.lower()] = canonical
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias.lower()] = canonical

def normalize_skill(skill_str: str) -> str:
    """Map any skill alias or variant to its canonical taxonomy name."""
    s = skill_str.strip().lower()
    return ALIAS_TO_CANONICAL.get(s, s)

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skills present in text using boundary-safe regex pattern matching
    against the taxonomy.
    """
    if not text:
        return []
        
    text_lower = f" {text.lower()} "
    found_skills: Set[str] = set()

    for canonical, aliases in SKILL_TAXONOMY.items():
        for alias in aliases:
            # Word boundary regex with special character handling (e.g. c++, c#, .net)
            escaped = re.escape(alias)
            # Match if surrounded by word boundaries, punctuation, or whitespaces
            pattern = rf'(?:^|[\s,.;:()/\-\[\]]){escaped}(?:[\s,.;:()/\-\[\]]|$)'
            if re.search(pattern, text_lower):
                found_skills.add(canonical)
                break

    return sorted(list(found_skills))

def match_skills(required_skills: List[str], preferred_skills: List[str], candidate_skills: List[str]) -> Tuple[List[str], List[str], List[str], float]:
    """
    Compute matched, missing, and extra skills along with a match score (0-100).
    """
    cand_norm = {normalize_skill(s) for s in candidate_skills}
    req_norm = [normalize_skill(s) for s in required_skills if s.strip()]
    pref_norm = [normalize_skill(s) for s in preferred_skills if s.strip()]

    matched_req = [s for s in req_norm if s in cand_norm]
    missing_req = [s for s in req_norm if s not in cand_norm]
    
    matched_pref = [s for s in pref_norm if s in cand_norm]
    
    # Extra skills candidate has beyond job requirements
    all_job_skills = set(req_norm + pref_norm)
    extra_skills = sorted(list(cand_norm - all_job_skills))

    # Calculate skill score
    total_req_count = len(req_norm)
    total_pref_count = len(pref_norm)

    if total_req_count == 0 and total_pref_count == 0:
        score = 80.0 if candidate_skills else 50.0
    else:
        req_weight = 0.85 if total_pref_count > 0 else 1.0
        pref_weight = 0.15 if total_pref_count > 0 else 0.0

        req_score = (len(matched_req) / total_req_count * 100.0) if total_req_count > 0 else 100.0
        pref_score = (len(matched_pref) / total_pref_count * 100.0) if total_pref_count > 0 else 100.0

        score = (req_score * req_weight) + (pref_score * pref_weight)

    all_matched = sorted(list(set(matched_req + matched_pref)))
    all_missing = sorted(list(set(missing_req)))

    return all_matched, all_missing, extra_skills, round(min(score, 100.0), 2)
