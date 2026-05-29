import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = 'database.db'
SCHEMA_PATH = 'schema.sql'

def init_db():
    print("Initializing the database...")
    
    # Establish connection
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Execute schema.sql
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        cursor.executescript(schema)
        print("Schema applied successfully.")
    else:
        print(f"Error: Schema file '{SCHEMA_PATH}' not found!")
        conn.close()
        return

    # Check and insert default Admin account
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        username = 'admin'
        password = 'admin123'
        password_hash = generate_password_hash(password)
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", (username, password_hash))
        print(f"Default admin created. Username: '{username}', Password: '{password}'")
    else:
        print("Admin account already exists.")

    # Check and insert sample FAQs
    cursor.execute("SELECT COUNT(*) FROM faqs")
    if cursor.fetchone()[0] == 0:
        sample_faqs = [
            # Admissions
            (
                "Admissions",
                "How do I apply for admissions at the college?",
                "You can apply online through our official admissions portal at https://admissions.college.edu. Simply register with your email, fill out the application form, upload the required documents, and pay the application fee of $50 (INR 1000) online. Physical forms are also available at the campus Administrative Block.",
                "apply, admissions, register, online portal, application form, adm block"
            ),
            (
                "Admissions",
                "What are the eligibility criteria for B.Tech/Engineering admissions?",
                "Candidates must have passed 10+2 (High School) or equivalent examination with Physics, Mathematics, and Chemistry/Computer Science as compulsory subjects. A minimum aggregate of 60% is required, alongside qualifying scores in national or state engineering entrance exams (like JEE Main).",
                "eligibility, btech, engineering, requirements, high school, 10+2, percent, jee"
            ),
            (
                "Admissions",
                "What documents are required during the admission process?",
                "The following documents are mandatory for verification:\n1. 10th and 12th Marksheets and Certificates\n2. Entrance Exam Scorecard (e.g., JEE)\n3. Transfer Certificate (TC) & Migration Certificate\n4. Character Certificate\n5. Category/Community Certificate (if applicable)\n6. 6 Passport-size photographs\n7. Aadhaar Card or national ID proof.",
                "documents, paperwork, certificate, verification, marksheets, photo, id, transfer"
            ),
            (
                "Admissions",
                "Is there a direct admission or management quota?",
                "Yes, a limited number of seats (up to 15%) are reserved under the Management Quota for direct admission. Candidates must satisfy the minimum eligibility criteria (60% in PCM in 12th). Interested applicants should contact the Admissions Office directly for seat availability and fee structures.",
                "direct admission, management quota, seats, non-entrance, direct"
            ),
            (
                "Admissions",
                "What is the last date to submit the application form for the upcoming session?",
                "The last date for submitting online applications for undergraduate courses is July 15th, 2026. For postgraduate programs, the deadline is July 30th, 2026. Please check our Admissions Announcement board regularly for any extensions.",
                "last date, deadline, submission, date, calendar, undergraduate, postgraduate"
            ),
            
            # Courses
            (
                "Courses",
                "What undergraduate B.Tech engineering branches are offered?",
                "We offer B.Tech programs in four core branches:\n1. Computer Science & Engineering (CSE) - Specializations in AI/ML & Cyber Security\n2. Electronics & Communication Engineering (ECE)\n3. Mechanical Engineering (ME)\n4. Civil Engineering (CE)\nEach program is a 4-year, full-time curriculum approved by the academic council.",
                "branches, btech, engineering, cse, ece, mechanical, civil, branches, majors"
            ),
            (
                "Courses",
                "Do you offer postgraduate programs like M.Tech or MBA?",
                "Yes, we offer 2-year full-time postgraduate degrees: \n- M.Tech in Computer Science & Engineering and VLSI Design. \n- MBA with specializations in Finance, Marketing, Human Resources, and Data Analytics. \nEligibility requires a valid GATE score for M.Tech, and CAT/MAT/GMAT scores for MBA admissions.",
                "postgraduate, pg, mtech, mba, masters, gate, cat, business, master"
            ),
            (
                "Courses",
                "What is the curriculum structure for Computer Science Engineering?",
                "The B.Tech CSE program spans 8 semesters, covering core topics like Data Structures, Algorithms, DBMS, Operating Systems, Computer Networks, and Software Engineering. Electives include AI/ML, Cloud Computing, Blockchain, and Full-Stack Development. The final year involves an industry-sponsored project and internship.",
                "curriculum, cse, courses, subjects, computer science, syllabus, semesters"
            ),
            (
                "Courses",
                "Are there any value-added certification courses offered?",
                "Yes, the college has active partnerships with industry leaders (AWS Academy, Cisco Networking Academy, Microsoft, and Oracle). We offer hands-on certification training in Cloud Architecture, Cyber Security, Salesforce, and Data Analytics, integrated directly with the regular academic timetable.",
                "certifications, industry, aws, oracle, cisco, training, value added, extra courses"
            ),
            
            # Fees
            (
                "Fees",
                "What is the annual tuition fee for B.Tech Computer Science Engineering?",
                "The annual tuition fee for B.Tech CSE is $2,500 (INR 2,00,000) for general merit students. In addition, there is a one-time examination and laboratory deposit fee of $150 (INR 12,000) payable at the time of admission. Management quota fees differ.",
                "fees, tuition, cost, btech, cse, price, annual, engineering"
            ),
            (
                "Fees",
                "Is there a hostel fee separate from tuition fees?",
                "Yes, hostel accommodation and mess facilities are separate from academic tuition. The annual hostel fee is $1,200 (INR 95,000) for a standard triple-sharing room, including 4 meals a day. Double-sharing and AC rooms are available at a premium rate.",
                "hostel fee, mess fee, accommodation cost, food price, rent"
            ),
            (
                "Fees",
                "What are the payment modes available for fee submission?",
                "Fees can be paid online via Net Banking, Credit/Debit cards, UPI, or through our student ERP portal. Alternatively, you can pay via Demand Draft (DD) drawn in favor of 'College Director of Accounts' payable at the campus bank branch. Cash payments are not accepted for academic fees.",
                "payment, modes, card, net banking, upi, dd, demand draft, deposit, online pay"
            ),
            (
                "Fees",
                "Are there any scholarships available for meritorious students?",
                "Yes! We offer extensive merit-based scholarships:\n1. 100% Tuition Fee Waiver for State/National Board toppers.\n2. 50% Tuition Fee Waiver for students with >95% marks in 10+2.\n3. 25% Tuition Fee Waiver for students scoring in the top 500 in the regional entrance exam.\nNeed-based financial aid is also available for economically disadvantaged students upon presenting income certificates.",
                "scholarships, waiver, discounts, free, merit, financial aid, concessions, poor"
            ),
            (
                "Fees",
                "Is there a fee refund policy if I withdraw my admission?",
                "Yes, our refund policy follows strict government regulations. If you withdraw before the commencement of classes, 100% of the tuition fee is refunded (minus a $15/INR 1000 processing charge). If you withdraw within 15 days after classes start, 80% is refunded. No refund is granted after 30 days of the session startup.",
                "refund, withdraw, cancel admission, money back, return"
            ),
            
            # Placements
            (
                "Placements",
                "What are the placement statistics for the last academic year?",
                "For the 2024-2025 batch, our college recorded an outstanding 94% placement rate for eligible students. Over 150 recruiters visited the campus. The highest international package was $60,000 (INR 48 LPA) and the average package was $8,500 (INR 6.8 LPA).",
                "placement stats, statistics, jobs, percentage, hired, hired rate, salary"
            ),
            (
                "Placements",
                "Which top companies visit the campus for placements?",
                "Our regular recruiters include major global and national tech leaders: Google, Amazon, Microsoft, TCS, Infosys, Wipro, Cognizant, Accenture, Capgemini, and HCL. We also host core engineering firms like Larsen & Toubro, Tata Motors, and Bosch for core departments.",
                "companies, recruiters, google, amazon, microsoft, tcs, infosys, employers, visit"
            ),
            (
                "Placements",
                "Does the college offer internship support?",
                "Yes, our Training & Placement Cell works actively to secure summer and winter internships. Students are eligible for internships from the 6th semester onwards. Many companies offer Pre-Placement Offers (PPOs) based on student performance during their internships.",
                "internship, stipend, summer training, ppo, industrial training, placement cell"
            ),
            (
                "Placements",
                "Who is the placement cell officer and how do I contact them?",
                "The Head of Training and Placements is Dr. Rajesh Sharma. You can contact the placement cell via email at placements@college.edu, or visit them in the Career Development Block, Ground Floor, between 10:00 AM and 4:00 PM.",
                "placement officer, contact placement, sharma, email, placement cell"
            ),
            
            # Exams
            (
                "Exams",
                "When are the semester exams usually conducted?",
                "Semester examinations are held twice a year:\n- Odd Semester (Sem 1, 3, 5, 7) exams are held in November/December.\n- Even Semester (Sem 2, 4, 6, 8) exams are held in April/May.\nPractical examinations and viva-voce are conducted 10 days prior to the written exams.",
                "semester exams, dates, months, timetable, scheduling, practicals, test"
            ),
            (
                "Exams",
                "Where can I view the exam timetable and schedule?",
                "The exam schedule is officially published on the Student ERP Portal under the 'Examinations' tab 30 days before the exam start date. A physical copy is also pinned on the Department Notice Boards.",
                "timetable, exam schedule, datesheet, time table, exam portal"
            ),
            (
                "Exams",
                "What is the passing criteria for semester exams?",
                "To pass a subject, a student must secure a minimum of 40% marks in the End-Semester Examination and a combined aggregate of 45% (including internal assessment, tests, and assignments) for that course. A minimum of 75% attendance is mandatory to sit for the exams.",
                "passing marks, pass, percentage, internal, attendance, fail, criteria"
            ),
            (
                "Exams",
                "How do I apply for a duplicate marksheet or transcript?",
                "You can request transcripts by applying online through the Student ERP portal or by writing an application to the Controller of Examinations. A fee of $5 (INR 400) per copy is applicable, and standard processing takes 7 to 10 working days.",
                "transcript, marksheet, duplicate certificate, controller of exams, degree"
            ),
            (
                "Exams",
                "What is the procedure for exam paper revaluation?",
                "Students unsatisfied with their results can apply for copy revaluation or re-totaling within 15 days of result declaration. The application form is available at the Exam Cell. A fee of $12 (INR 1000) per subject is charged. Results of revaluation are declared within 4 weeks.",
                "revaluation, recheck, recount, marks change, paper review, result issue"
            ),
            
            # Hostel
            (
                "Hostel",
                "What hostel facilities are available for boys and girls?",
                "We have separate, secured residential blocks for boys and girls inside the campus. Facilities include 24/7 high-speed Wi-Fi, laundry service, continuous electricity and water supply, recreation rooms with TVs, gymnasiums, and round-the-clock security surveillance.",
                "hostel facilities, boys hostel, girls hostel, rooms, laundry, wifi, gym, security"
            ),
            (
                "Hostel",
                "Are AC rooms available in the hostel?",
                "Yes, we offer both single and double sharing Air-Conditioned (AC) rooms. AC room allocations are done on a first-come, first-served basis during admission. They carry an additional utility fee of $300 (INR 25,000) per year to cover electrical usage.",
                "ac rooms, air conditioner, single room, cooling, premium room"
            ),
            (
                "Hostel",
                "What is the mess menu and quality of food?",
                "The mess provides nutritious vegetarian and non-vegetarian food options. The menu changes weekly and includes breakfast, lunch, high tea, and dinner. The food committee, comprising student hostel representatives, regularly inspects quality and hygiene.",
                "food quality, mess menu, kitchen, vegetarian, non-veg, breakfast, dinner, meals"
            ),
            (
                "Hostel",
                "What are the hostel rules and curfew timings?",
                "Hostel security is highly prioritized. The main gate curfew timing is 9:30 PM for all students. Residents must obtain permission from the Warden (using the Outing Pass App) for night-outs or weekend leaves. Ragging is strictly prohibited and carries severe penalties.",
                "rules, curfew, timing, warden, ragging, safety, night-out, permission"
            ),
            
            # General
            (
                "General",
                "What is the college address and contact information?",
                "The campus is located at: 100 Innovation Boulevard, Tech City, Sector-5. \nContact numbers: +1 (555) 019-2830 / +91 11 2345 6789. \nFor general queries, email info@college.edu. For admin offices, visit during office hours: 9:00 AM to 5:00 PM, Monday to Saturday.",
                "address, contact, location, phone, email, map, directions, working hours"
            ),
            (
                "General",
                "What are the library timings and membership rules?",
                "The Central Library is open from 8:00 AM to 9:00 PM on weekdays, and 9:00 AM to 5:00 PM on Sundays. During exam periods, the reading rooms are open 24/7. All registered students get a library card allowing them to borrow up to 4 books for 14 days.",
                "library hours, books, borrow, reading room, study, library card"
            ),
            (
                "General",
                "Are there sports facilities on campus?",
                "Absolutely! We have state-of-the-art sports facilities including an Olympic-sized swimming pool, an indoor sports complex (for badminton, table tennis, squash), a grass football field, a cricket stadium, and synthetic tennis and basketball courts. Annual sports tournaments are held in January.",
                "sports, gym, swimming pool, cricket, football, court, games, athletics"
            ),
            (
                "General",
                "Does the college provide bus/transport services?",
                "Yes, the college runs a fleet of 15 air-conditioned buses connecting all major residential areas of the city to the campus. Students can subscribe to the annual transport service on the ERP portal. Bus passes are issued on a semester-wise basis.",
                "transport, bus routes, pick up, transit, pass, shuttle, travel"
            )
        ]
        
        cursor.executemany(
            "INSERT INTO faqs (category, question, answer, tags) VALUES (?, ?, ?, ?)",
            sample_faqs
        )
        print(f"Pre-seeded the database with {len(sample_faqs)} highly detailed college FAQs.")
    else:
        print("FAQs table already has data. Skipping seed.")

    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database initialization completed successfully!")

if __name__ == '__main__':
    init_db()
