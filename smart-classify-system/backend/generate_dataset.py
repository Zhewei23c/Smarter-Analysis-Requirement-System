import csv
import random


fr_actors = ["The system", "The application", "The platform", "The user interface", "The API", "The admin module", "The mobile app", "The backend server", "The smart watch"]
fr_verbs = ["shall allow", "must enable", "will support", "should provide", "shall permit", "must facilitate", "allows", "enables", "is designed to let", "automatically"]
fr_users = ["users", "students", "tutors", "administrators", "guests", "customers", "clients", "moderators", "parents", "staff", "doctors", "patients", "drivers"]
fr_actions = [
    "to register an account", "to log in securely", "to reset their password", "to update profile details",
    "to search for courses", "to filter results by price", "to book a session", "to cancel an appointment",
    "to upload assignments", "to download materials", "to view transaction history", "to generate invoices",
    "to receive notifications", "to chat with support", "to rate the tutor", "to submit feedback",
    "to manage content", "to configure settings", "to export data to PDF", "to import user lists",
    "to schedule a meeting", "to record the session", "to share the screen", "to mute the microphone",
    "to calculate tax", "to track GPS location", "to scan QR codes", "to verify identity"
]

fr_conditions = [
    "via email", "using a secure form", "in real-time", "after validation", 
    "before session starts", "within the dashboard", "automatically", "manually",
    "using 2FA", "through the web portal", "via SMS", "without refreshing the page",
    "using the mobile app", "securely"
]
nfr_subjects = [
    "The system", "The database", "The login page", "The API response", "All user data", "Password storage", 
    "The network connection", "The server", "Data backups", "Security protocols", "Response time", "Availability",
    "The mobile application", "Transaction processing"
]
nfr_constraints = [
    "must respond within 2 seconds", "shall have an uptime of 99.9%", "must be encrypted using AES-256",
    "shall support 10,000 concurrent users", "must comply with GDPR", "shall be compatible with Chrome and Edge",
    "must be accessible to screen readers (WCAG 2.1)", "shall auto-backup every 24 hours", "must allow recovery within 5 minutes",
    "shall use HTTPS for all communications", "must be modular and maintainable", "should have comprehensive documentation",
    "must load within 3 seconds", "shall adhere to ISO 27001", "must be protected against SQL injection",
    "must support multi-language (i18n)", "shall operate on low-bandwidth networks", "must failover gracefully"
]

noise_junk = ["Chapter", "Section", "Table of Contents", "Page", "Figure", "Note:", "Source:", "Q:", "A:", "Abstract", "Introduction", "References", "Appendix"]

# --- Functional Requirements (FR) ---
manual_fr = [
    # E-commerce
    "The system shall allow users to add items to the shopping cart.",
    "Users must be able to proceed to checkout as a guest.",
    "The application shall calculate shipping costs based on weight.",
    "The system will send an order confirmation email automatically.",
    "Admins shall be able to update product inventory levels.",
    "Customers can track their order status via a tracking number.",
    "The system must allow users to apply discount coupons.",
    "The platform shall support payment via Credit Card and PayPal.",
    "Users shall be able to write reviews for purchased products.",
    "The system provides a recommendation engine for related products.",
    
    # Healthcare / Medical
    "The system shall allow doctors to view patient medical history.",
    "Patients must be able to book appointments online.",
    "The app allows nurses to record vital signs.",
    "The system shall generate a prescription PDF.",
    "Admins can manage hospital bed availability.",
    "The system must alert doctors of potential drug interactions.",
    "Users shall be able to upload MRI scan results.",
    "The platform supports telemedicine video calls.",
    "The system shall track vaccination schedules.",
    "Patients can request a refill for their medication.",

    # Banking / FinTech
    "The system shall allow users to transfer funds between accounts.",
    "Users must be able to view their monthly bank statements.",
    "The app allows customers to freeze their credit card instantly.",
    "The system shall calculate interest rates for savings accounts.",
    "Admins can approve or reject loan applications.",
    "The platform must support multi-currency transactions.",
    "Users shall be able to set spending limits.",
    "The system sends push notifications for suspicious activity.",
    "Customers can scan checks for mobile deposit.",
    "The system shall generate tax reports for the fiscal year.",

    # Education (LMS)
    "The system shall allow students to submit assignments before the deadline.",
    "Tutors must be able to grade submissions and provide feedback.",
    "The platform allows users to enroll in courses.",
    "The system shall track student attendance automatically.",
    "Admins can manage the academic calendar.",
    "Users shall be able to download course materials offline.",
    "The system provides a discussion forum for each class.",
    "Students can view their GPA and transcript.",
    "The app allows parents to view their child's progress.",
    "The system shall issue a certificate upon course completion.",

    # Social Media / General
    "The system shall allow users to upload profile pictures.",
    "Users must be able to block other users.",
    "The app allows users to post status updates.",
    "The system shall support direct messaging between users.",
    "Admins can moderate reported content.",
    "Users shall be able to like and comment on posts.",
    "The platform supports logging in via Facebook or Google.",
    "The system shall allow users to change their privacy settings.",
    "Users can search for friends by name or email.",
    "The system allows users to create groups and events.",
    
    # IoT / Smart Home
    "The system shall allow users to adjust the thermostat remotely.",
    "The app must notify the user if the door is left open.",
    "Users can set schedules for smart lights.",
    "The system shall display real-time energy consumption.",
    "The camera must start recording when motion is detected.",
    
    # Simple sentences
    "User logs in.",
    "Admin adds a user.",
    "System sends email.",
    "Calculate the total.",
    "Display the results.",
    "Print the receipt.",
    "Save the file.",
    "Edit the record.",
    "Delete the account.",
    "Search for item."
] * 2  # Double the list to reach ~100

# --- Non-Functional Requirements (NFR) ---
manual_nfr = [
    # Performance
    "The system must load the homepage within 2 seconds.",
    "The database shall handle 500 transactions per second.",
    "The API response time must not exceed 200ms.",
    "The application shall support 50,000 concurrent users.",
    "Images must be compressed to reduce bandwidth usage.",
    "The system should optimize queries to prevent latency.",
    "The mobile app must launch within 3 seconds.",
    "Video streaming shall support 4K resolution without buffering.",
    "The system must handle peak load during Black Friday.",
    "CPU usage shall not exceed 80% under normal load.",

    # Security
    "All user passwords must be hashed using Bcrypt.",
    "The system shall enforce Two-Factor Authentication (2FA).",
    "Data at rest must be encrypted using AES-256.",
    "The platform must comply with GDPR and CCPA regulations.",
    "The system shall lock the account after 5 failed login attempts.",
    "Communication must occur over a secure HTTPS channel.",
    "The API must be protected against SQL injection attacks.",
    "Sessions shall time out after 15 minutes of inactivity.",
    "Access to the admin panel must be restricted by IP address.",
    "The system shall maintain an audit log of all actions.",

    # Availability / Reliability
    "The system shall guarantee 99.99% uptime.",
    "Scheduled maintenance must perform during non-business hours.",
    "The system shall recover from a crash within 5 minutes.",
    "Data backups must be performed automatically every night.",
    "The platform must have a disaster recovery plan.",
    "The system shall support failover to a secondary server.",
    "The application must not lose data during a power outage.",
    "Service availability is monitored 24/7.",
    "The system shall notify admins immediately upon failure.",
    "Reliability must be ensuring through redundant storage.",

    # Usability / Accessibility
    "The UI must be intuitive and easy to navigate.",
    "The system shall support English, Spanish, and French.",
    "The application must be compatible with screen readers (WCAG).",
    "The font size shall be adjustable for visually impaired users.",
    "The system must provide tooltips for complex features.",
    "Error messages must be clear and user-friendly.",
    "The mobile app shall support Dark Mode.",
    "The design must be responsive across all device sizes.",
    "Users should be able to complete checkout in 3 clicks.",
    "The help documentation must be accessible from any page.",

    # Scalability / Maintainability / Portability
    "The system architecture must be microservices-based.",
    "The code shall be well-documented for future developers.",
    "The system must scale horizontally using Kubernetes.",
    "The application shall run on Windows, Linux, and macOS.",
    "The database must support sharding for future growth.",
    "The system shall use standard APIs for integration.",
    "The mobile app must work on iOS 12+ and Android 8+.",
    "Modules must be loosely coupled to allow easy updates.",
    "The software shall be deployable via Docker containers.",
    "The system must support cloud deployment on AWS or Azure."
] * 2

# --- Unknown / Noise / Background (Unknown) ---
manual_unknown = [
    # Document Structure
    "Table of Contents",
    "List of Figures",
    "List of Tables",
    "1. Introduction",
    "2. Methodology",
    "3. System Design",
    "4. Conclusion",
    "Appendix A",
    "References",
    "Page 1 of 50",
    "Version 1.0",
    "Author: John Doe",
    "Date: 2024-01-01",
    "Copyright 2024",
    "Confidential Document",

    # Explanatory Text (Not Requirements)
    "The purpose of this document is to outline the scope.",
    "We interviewed 10 stakeholders to gather information.",
    "The current system is outdated and slow.",
    "Figure 3 shows the data flow diagram.",
    "As seen in Table 2, the costs are rising.",
    "This project aims to solve the problem of manual entry.",
    "The waterfall model was chosen for development.",
    "Stakeholders agreed on the following terms.",
    "The meeting was held on Monday.",
    "There are three main modules in the system.",
    
    # Fragments / Garbage
    "Q:",
    "A:",
    "Yes.",
    "No.",
    "Maybe.",
    "10.",
    "......",
    "-----",
    "Note:",
    "Source:",
    "User Story 1",
    "Scenario A",
    "Click here",
    "http://www.example.com",
    "email@address.com",
    "Lorem ipsum dolor sit amet",
    "Functionality",
    "Non-Functional Attributes",
    
    # Definitions
    "API stands for Application Programming Interface.",
    "HTML is a markup language.",
    "The server is located in New York.",
    "Python is the programming language used.",
    "The database uses MySQL.",
    
    # Tricky ones (Look like reqs but are not)
    "This is a functional requirement.", 
    "We hope the system will be fast.",
    "It would be nice to have.",
    "The users like the new design.",
    "We suggest using React.",
    "The problem with the old app.",
    "Analysis of the requirements."
] * 2


def generate_dataset(filename="dataset.csv"):
    data = []
    

    target_fr = 50000 
    target_nfr = 50000
    target_unknown = 80000

    print(f"🚀 Starting generation...")


    for _ in range(target_fr):
        s = f"{random.choice(fr_actors)} {random.choice(fr_verbs)} {random.choice(fr_users)} {random.choice(fr_actions)} {random.choice(fr_conditions)}."
        data.append((s, "FR"))
    
    for _ in range(target_nfr):
        s = f"{random.choice(nfr_subjects)} {random.choice(nfr_constraints)}."
        data.append((s, "NFR"))
        
    for _ in range(target_unknown):
        s = f"{random.choice(noise_junk)} {random.randint(1,999)} {random.choice(['.', '', '...'])}"
        data.append((s, "Unknown"))

    for s in manual_fr:
        data.append((s, "FR"))
    
    for s in manual_nfr:
        data.append((s, "NFR"))
        
    for s in manual_unknown:
        data.append((s, "Unknown"))

    print("💾 Saving to CSV...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["text", "label"])
            
            random.shuffle(data)
            writer.writerows(data)
            
        print(f"✅ DONE! Generated {len(data)} samples.")
        print(f"   - Manual FR: ~{len(manual_fr)}")
        print(f"   - Manual NFR: ~{len(manual_nfr)}")
        print(f"   - Manual Unknown: ~{len(manual_unknown)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_dataset()