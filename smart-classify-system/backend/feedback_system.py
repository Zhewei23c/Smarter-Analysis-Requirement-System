import json
import os
from datetime import datetime, timedelta

SUBMISSIONS_FILE = 'submissions.json'
DATASET_FILE = 'dataset.csv'
USERS_FILE = 'users.json' 


MAX_VOTE_CHANGES = 3  
EXPIRATION_HOURS = 24 


def load_json(filename):
    if not os.path.exists(filename): return [] if filename == SUBMISSIONS_FILE else {}
    with open(filename, 'r') as f:
        try: return json.load(f)
        except: return [] if filename == SUBMISSIONS_FILE else {}

def save_submissions(data):
    with open(SUBMISSIONS_FILE, 'w') as f: json.dump(data, f, indent=4)

def get_total_admins():
    users = load_json(USERS_FILE)
    if not users: return 5 
    
    admin_count = 0
    for u in users.values():
        if u.get('role') == 'admin':
            admin_count += 1
    return admin_count

def load_submissions():
    return load_json(SUBMISSIONS_FILE)

def add_submission(text, req_type, system_type, user):
    submissions = load_submissions()
    new_sub = {
        "id": str(len(submissions) + 1000), 
        "text": text, "type": req_type, "system_type": system_type,
        "submitted_by": user, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending", "final_decision_reason": "",
        "votes": {"approve": [], "reject": []},
        "vote_tracking": {} 
    }
    submissions.append(new_sub)
    save_submissions(submissions)
    return True

def vote_submission(sub_id, admin_user, vote_type): 
    submissions = load_submissions()
    target = None
    for sub in submissions:
        if sub['id'] == sub_id: target = sub; break
    
    if not target: return False, "Submission not found."
    
    check_expired() 
    
    submissions = load_submissions()
    for sub in submissions:
        if sub['id'] == sub_id: target = sub; break
        
    if target['status'] != 'pending': 
        return False, "This submission is closed or expired."

    if 'vote_tracking' not in target: target['vote_tracking'] = {}
    current_changes = target['vote_tracking'].get(admin_user, 0)

    if admin_user in target['votes'][vote_type]:
        return False, "You already voted for this option."

    opposite_type = 'reject' if vote_type == 'approve' else 'approve'
    msg = ""
    
    if admin_user in target['votes'][opposite_type]:
        if current_changes >= MAX_VOTE_CHANGES:
            return False, f"Limit reached. You have used all {MAX_VOTE_CHANGES} changes."
        
        target['votes'][opposite_type].remove(admin_user)
        target['votes'][vote_type].append(admin_user)
        target['vote_tracking'][admin_user] = current_changes + 1
        
        remaining = MAX_VOTE_CHANGES - (current_changes + 1)
        msg = f"Vote changed to {vote_type.upper()}. ({remaining} changes left)"
    else:
        target['votes'][vote_type].append(admin_user)
        if admin_user not in target['vote_tracking']:
            target['vote_tracking'][admin_user] = 0
            
        msg = "Vote recorded successfully."

    total_admins = get_total_admins()
    majority_threshold = (total_admins // 2) + 1 
    
    approve_count = len(target['votes']['approve'])
    reject_count = len(target['votes']['reject'])
    
    if approve_count >= majority_threshold:
        _finalize(target, 'approved', f"Approved by Majority ({approve_count}/{total_admins})")
        msg = "Submission Approved!"
    elif reject_count >= majority_threshold:
        _finalize(target, 'rejected', f"Rejected by Majority ({reject_count}/{total_admins})")
        msg = "Submission Rejected."
        
    save_submissions(submissions)
    return True, msg

def _finalize(submission, status, reason):
    submission['status'] = status
    submission['final_decision_reason'] = reason
    
    if status == 'approved':
        _append_to_dataset(submission['text'], submission['type'], submission['system_type'])

def _append_to_dataset(text, label, domain):
    try:
        file_exists = os.path.isfile(DATASET_FILE)
        with open(DATASET_FILE, 'a', newline='', encoding='utf-8') as f:
            import csv
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['text', 'label', 'system_type'])
            writer.writerow([text, label, domain])
    except Exception as e:
        print(f"Error appending to dataset: {e}")

def check_expired():
    submissions = load_submissions()
    changed = False
    now = datetime.now()
    
    for sub in submissions:
        if sub['status'] == 'pending':
            try:
                sub_time = datetime.strptime(sub['timestamp'], "%Y-%m-%d %H:%M:%S")
                
                if now - sub_time > timedelta(hours=EXPIRATION_HOURS):
                    approve_c = len(sub['votes']['approve'])
                    reject_c = len(sub['votes']['reject'])
                    
                    if approve_c > reject_c:
                        _finalize(sub, 'approved', "Approved (Time Expired - Majority Vote)")
                    elif reject_c > approve_c:
                        _finalize(sub, 'rejected', "Rejected (Time Expired - Majority Vote)")
                    else:
                        _finalize(sub, 'rejected', "Rejected (Time Expired - Tie Vote)")
                    
                    changed = True
            except ValueError:
                continue 
                
    if changed: save_submissions(submissions)