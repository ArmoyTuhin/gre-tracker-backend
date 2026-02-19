# GRE Error Tracker – Backend API

FastAPI backend for the GRE Error Tracker application, featuring a spaced repetition system (SRS) powered by the SM-2 algorithm.

---

## Overview

This API helps track GRE mistakes, manage vocabulary, run exam sessions, and schedule reviews intelligently using spaced repetition. It is designed for structured and efficient GRE preparation.

---

## Core Features

- Mistake Management (CRUD + filters)
- Spaced Repetition Scheduling (SM-2)
- Daily Review System (Quant & Verbal separation)
- Mastery Tracking (after 5 successful reviews)
- Vocabulary Management
- Exam Sessions with statistics
- Export to Excel and PDF

---

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL / SQLite
- SM-2 Algorithm
- OpenPyXL
- ReportLab

---

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL (optional)

### Setup

```bash
git clone <repo-url>
cd gre-tracker-backend

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env  # optional
