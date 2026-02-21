# OpportunityHub — Opportunity Aggregation Platform

## 📌 Project Overview

Ivy Intelligence is a web-based platform that automatically aggregates academic and career opportunities from multiple trusted sources such as Indian academic portals, global opportunity feeds, and institutional websites.  
The system uses web scraping and intelligent content processing to present structured, searchable, and user-friendly opportunity listings.

The platform helps students and professionals easily discover internships, fellowships, scholarships, research programs, and training opportunities in one centralized location.

---

## 🎯 Problem Statement

Students often struggle to track opportunities scattered across multiple websites. Manual searching is time-consuming and inefficient.

This project solves that problem by:

- Automatically collecting opportunities
- Filtering and organizing them
- Showing deadlines and urgency
- Allowing users to search, save, and track opportunities

---

## 🚀 Key Features

- 🌐 Multi-source web scraping (India + Global + Institutional)
- 🔍 Smart keyword search
- 🧠 Opportunity type classification (Internship, Fellowship, Scholarship, etc.)
- 📅 Automatic deadline extraction with urgency indicator
- ⭐ Bookmark / Save opportunities
- 📊 Dashboard analytics (India vs Global distribution, total, saved, last updated)
- 📄 Pagination for scalability
- 🧠 Smart ranking (deadline + relevance + freshness)
- 🔔 Automated background scraping scheduler
- 📖 Clean detailed opportunity view with full content extraction
- 🎨 Responsive Bootstrap UI
- 🏠 Landing page with project overview

---

## 🏗 System Architecture


Scrapers (India / Global / Institutional)
↓
Content Extraction + Cleaning
↓
Classification + Deadline Detection
↓
Database (SQLite)
↓
Django Backend (Views / Services)
↓
Frontend (Bootstrap UI)
↓
User Interaction (Search / Save / Filter / Apply)


---

## 🧪 Technologies Used

- Python
- Django
- BeautifulSoup (Web Scraping)
- Requests
- APScheduler (Automation)
- SQLite
- Bootstrap (Frontend)
- Regex + Date Parsing

---

## ⚙️ How to Run the Project

1. Clone repository
2. Create virtual environment
3. Install dependencies

```bash
pip install -r requirements.txt
```

Run migrations
```
python manage.py migrate
```

Start server
```
python manage.py runserver
```
Open browser
```
http://127.0.0.1:8000/
```
## 🔄 Automated Scraping

The system automatically updates opportunities using a background scheduler.
Users can also manually refresh opportunities from the interface.

## 📈 Future Scope

- User authentication & personalized recommendations

- Email / notification alerts for new opportunities

- AI-based opportunity ranking

- Advanced filtering (country, field, eligibility)

- Deployment to cloud

- REST API support

- Mobile-friendly progressive web app

## 👨‍💻 Author

Karthik Byri
B.Tech Computer Science & Engineering
