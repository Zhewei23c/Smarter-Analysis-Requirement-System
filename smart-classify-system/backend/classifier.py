import os
import joblib
import pdfplumber
import re
from docx import Document

def clean_text(text):
    if not text: return ""
    text = re.sub(r'[^\x20-\x7E]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_sentences(text):
    text = re.sub(r'(?<!\w)(\d+\.\s+|-\s+|•\s+|[A-Za-z]+-\d+\s+|FR\d+\s+|\d+(\.\d+)+\s+)', r'\n\1', text)

    chunks = text.split('\n')
    
    final_sentences = []
    
    for chunk in chunks:
        chunk = clean_text(chunk)
        if not chunk: continue

        role_match = re.search(r'(Role:.*?)(\d+(\.\d+)+\s+.*)', chunk, re.IGNORECASE)
        if role_match:
            chunk = role_match.group(2)

        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', chunk)
        
        for s in sentences:
            s = s.strip()
            if len(s) > 15 and len(s.split()) >= 3:
                final_sentences.append(s)
                
    return final_sentences

def is_noise(text):
    t = text.lower()
    if len(t) < 10: return True
    
    noise_keywords = [
        "page", "copyright", "total:", "marks", "student id", 
        "table of contents", "references", "appendix", "version", 
        "project title", "declaration", "supervisor", 
        "module key features", "payment processing", 
        "system overview", "boundary", "modules", 
        "functional requirements id description",
        "diagram", "figure", "chart", "abstract", "background"
    ]
    if any(k in t for k in noise_keywords): return True
    if re.search(r'\.{3,}', t): return True 
    if re.match(r'^(q|a|question|answer|interview|student|tutor)\s*[:\-\)]', t): return True
    return False

def has_action_verb(text):
    verbs = [
        "shall", "must", "will", "should", "can", "could",
        "allow", "allows", "enable", "enables", "provide", "provides",
        "support", "supports", "ensure", "ensures",
        "register", "login", "update", "delete", "view", "search", "pay", 
        "generate", "notify", "encrypt", "validate", "verify", "store",
        "load", "handle", "handles", "scale", "process", "processes", 
        "operate", "operates", "maintain", "maintains", "manage", "manages",
        "calculate", "calculates", "display", "displays"
    ]
    return any(v in text.lower().split() for v in verbs)

def extract_candidates(file_path):
    print(f"DEBUG: >>> v13.0 (PDF+Word) 处理: {file_path}")
    candidates = []
    seen_hashes = set()

    def add_candidate(raw_text, source, forced_type=None):
        raw_text = clean_text(raw_text)
        sentences = split_into_sentences(raw_text)
        
        for text in sentences:
            if is_noise(text): continue
            
            if not forced_type and not has_action_verb(text):
                continue

            text_hash = re.sub(r'\W', '', text.lower())
            if text_hash in seen_hashes: continue
            seen_hashes.add(text_hash)
            
            candidates.append({"text": text, "source": source, "forced_type": forced_type})

    try:
        if file_path.lower().endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row: continue
                            clean_row = [clean_text(str(c)) for c in row if c]
                            
                            row_type = None
                            row_text = None
                            for cell in clean_row:
                                if re.match(r'^(fr|nfr|req)[-\s]?\d+', cell.lower()):
                                    row_type = "Non-Functional" if "nfr" in cell.lower() else "Functional"
                                    if len(cell) > 20: row_text = cell 
                            
                            if not row_text and clean_row:
                                longest = max(clean_row, key=len)
                                if len(longest) > 20: row_text = longest
                            
                            if row_text:
                                add_candidate(row_text, "pdf_table", row_type)

                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        buffer = ""
                        current_forced_type = None
                        for line in lines:
                            clean_line = clean_text(line)
                            if not clean_line or is_noise(clean_line): continue
                            
                            id_match = re.match(r'^(fr|nfr|req)[-\s]?\d+', clean_line.lower())
                            if id_match:
                                if buffer: add_candidate(buffer, "pdf_text", current_forced_type)
                                buffer = clean_line
                                current_forced_type = "Non-Functional" if "nfr" in clean_line.lower() else "Functional"
                            else:
                                if not buffer: buffer = clean_line
                                else: buffer += " " + clean_line
                        if buffer: add_candidate(buffer, "pdf_text", current_forced_type)

        elif file_path.lower().endswith('.docx'):
            doc = Document(file_path)

            for para in doc.paragraphs:
                if para.text.strip():
                    add_candidate(para.text, "docx_text")

            for table in doc.tables:
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if not row_data: continue
                    
                    row_type = None
                    row_text = None
                    
                    for cell_text in row_data:
                         if re.match(r'^(fr|nfr|req)[-\s]?\d+', cell_text.lower()):
                            row_type = "Non-Functional" if "nfr" in cell_text.lower() else "Functional"
                            if len(cell_text) > 20: row_text = cell_text
                    
                    if not row_text and row_data:
                        longest = max(row_data, key=len)
                        if len(longest) > 20: row_text = longest
                    
                    if row_text:
                        add_candidate(row_text, "docx_table", row_type)

    except Exception as e:
        print(f"ERROR: 文件读取失败 -> {e}")
        return []

    return candidates

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'fr_nfr_model.pkl') 
vectorizer_path = os.path.join(current_dir, 'vectorizer.pkl')
model = None
vectorizer = None
try:
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        vectorizer = joblib.load(vectorizer_path)
except: pass

def classify_final(candidate):
    text = candidate["text"]
    forced_type = candidate["forced_type"]
    
    if forced_type: return forced_type, "Detected ID (e.g., FR-xx/NFR-xx)"

    text_lower = text.lower()
    
    nfr_keywords = [
        "availability", "security", "performance", "scalability", "usability", 
        "response time", "encryption", "throughput", "latency", "99.9%", 
        "load within", "concurrent users", "backup", "recovery", "compliance",
        "responsive", "mobile", "interface", "compatible", "browser", "ios", "android",
        "reliability", "maintainability", "portability"
    ]
    for k in nfr_keywords:
        if k in text_lower:
            return "Non-Functional", f"Contains NFR keyword: '{k}'"

    fr_keywords = [
        "system shall", "system must", "user shall", "admin shall", "can", 
        "able to", "register", "login", "update", "delete", "view", "search", 
        "pay", "manage", "track", "generate", "verify", "allow", "process", "handle"
    ]
    for k in fr_keywords:
        if k in text_lower:
            return "Functional", f"Contains Action verb: '{k}'"

    if model and vectorizer:
        try:
            vec = vectorizer.transform([text])
            probs = model.predict_proba(vec)[0]
            max_prob = max(probs)
            if max_prob > 0.6:
                pred = model.predict(vec)[0]
                label = str(pred).strip().lower()
                confidence_str = f"{int(max_prob * 100)}%"
                if label in ['fr', 'functional', '1']: 
                    return "Functional", f"AI Model Prediction (Confidence: {confidence_str})"
                if label in ['nfr', 'non-functional', '0']: 
                    return "Non-Functional", f"AI Model Prediction (Confidence: {confidence_str})"
        except: pass

    return "Unknown", "Low confidence"

def analyze_document_with_highlighting(file_path):
    candidates = extract_candidates(file_path)
    
    results = []
    fr_count = 0
    nfr_count = 0

    for cand in candidates:
        label, reason = classify_final(cand)
        
        if label in ["Functional", "Non-Functional"]:
            if label == "Functional": fr_count += 1
            else: nfr_count += 1
            
            results.append({
                "requirement": cand["text"], 
                "type": label, 
                "confidence": 1.0,
                "reason": reason
            })

    return {
        "requirements": results, 
        "functional_count": fr_count,
        "non_functional_count": nfr_count,
        "stats": {"FR": fr_count, "NFR": nfr_count}
    }

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'txt', 'docx'}