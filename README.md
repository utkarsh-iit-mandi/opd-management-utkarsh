Digital OPD Management System

A lightweight Digital OPD / Clinic Management System designed for small to medium healthcare facilities to digitize patient flow, consultations, payments, and medicine dispensing.

📌 Overview

Many clinics and OPDs still rely on manual registers or fragmented digital tools, leading to:

Long waiting times

Poor visit tracking

Billing inconsistencies

Errors in medicine dispensing

This project provides a simple, modular, web-based solution to manage OPD workflows efficiently.

✨ Features

Patient Registration

Unique patient records

Visit-wise history

Visit Management

Doctor assignment

Visit status tracking

Payment Register

Consultation fee entry

Date-wise records

Medicine Dispensing

Prescription-based dispensing

Basic stock handling

Analytics Dashboard

OPD count

Revenue overview

🛠️ Tech Stack

Frontend: HTML, CSS

Backend: Python (Flask)

Database: SQLite (local)

Server: Localhost (development mode)

📁 Project Structure
aggarwal_clinic/
│
├── app.py
├── analytics_dashboard.html
├── start_clinic.sh
├── templates/
├── .gitignore
└── README.md

🚀 How to Run Locally
1️⃣ Clone the repository
git clone https://github.com/utkarsh-iit-mandi/opd-management-utkarsh.git
cd opd-management-utkarsh

2️⃣ Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Run the application
python app.py

5️⃣ Open in browser
http://127.0.0.1:5000

🔐 Demo Credentials (Sample)
Role	Username	Password
Admin	admin	admin123

(Credentials are for demo/testing only)

⚠️ Notes

Database files and credentials are excluded from the repository for security reasons.

This project currently focuses on OPD-level management.

Not intended for production deployment in its current form.

🔮 Future Enhancements

Appointment scheduling system

Role-based access control

SMS / Email notifications

Inventory alerts

AI-based clinical decision support (future scope)

🎓 Academic Relevance

This project demonstrates:

Full-stack web development

Real-world database design

Practical system architecture

Healthcare workflow understanding

Suitable for courses in:

Software Engineering

Database Systems

Web Development

👤 Author

Utkarsh Aggarwal
B.Tech Mathematics & Computing
IIT Mandi

GitHub: https://github.com/utkarsh-iit-mandi

📜 License

This project is developed for academic and educational purposes.