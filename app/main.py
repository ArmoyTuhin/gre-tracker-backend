from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List
import sys
import os
import io

# Add parent directory to path to import utils
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import get_db, Base, engine
from app.models import GREMistake, ExamSession, Vocabulary
from app.schemas import GREMistakeCreate, GREMistakeResponse, ReviewSubmit, ReviewResponse, MistakeFilter, ExamSessionCreate, ExamSessionResponse, ExamAnswerSubmit, VocabularyCreate, VocabularyUpdate, VocabularyResponse
from utils.sm2 import calculate_next_review
from utils.export import export_to_excel, export_to_pdf, export_vocabulary_to_excel, export_vocabulary_to_pdf
from fastapi.responses import StreamingResponse

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GRE Error Tracker API", version="1.0.0")

# CORS configuration
# In production, replace with your actual Vercel frontend URL
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,https://your-vercel-app.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "GRE Error Tracker API"}

@app.post("/mistakes/", response_model=GREMistakeResponse)
async def create_mistake(mistake: GREMistakeCreate, db: Session = Depends(get_db)):
    """Create a new GRE mistake entry."""
    try:
        mistake_data = mistake.dict(exclude_none=False)
        # Convert empty strings to None for optional text fields
        for key in ['sub_topic', 'problem_statement_text', 'solution_text', 'what_did_i_do_wrong', 
                    'what_will_i_do_next_time', 'additional_techniques', 'relevant_concept']:
            if mistake_data.get(key) == '':
                mistake_data[key] = None
        # Ensure image URL lists are lists
        if mistake_data.get("problem_statement_image_urls") is None:
            mistake_data["problem_statement_image_urls"] = []
        if mistake_data.get("solution_image_urls") is None:
            mistake_data["solution_image_urls"] = []
        db_mistake = GREMistake(**mistake_data)
        db.add(db_mistake)
        db.commit()
        db.refresh(db_mistake)
        return db_mistake
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating mistake: {error_details}")
        raise HTTPException(status_code=400, detail=f"Failed to create mistake: {str(e)}")

@app.get("/mistakes/", response_model=List[GREMistakeResponse])
async def get_all_mistakes(
    section: str = None,
    topic: str = None,
    sub_topic: str = None,
    error_type: str = None,
    kmf_section: int = None,
    kmf_problem_set: int = None,
    mastered: bool = None,
    db: Session = Depends(get_db)
):
    """Get all mistakes with optional filtering."""
    query = db.query(GREMistake)
    
    # Apply filters
    if section:
        query = query.filter(GREMistake.section == section)
    if topic:
        query = query.filter(GREMistake.topic == topic)
    if sub_topic:
        query = query.filter(GREMistake.sub_topic == sub_topic)
    if error_type:
        query = query.filter(GREMistake.error_type == error_type)
    if kmf_section is not None:
        query = query.filter(GREMistake.kmf_section == kmf_section)
    if kmf_problem_set is not None:
        query = query.filter(GREMistake.kmf_problem_set == kmf_problem_set)
    if mastered is not None:
        query = query.filter(GREMistake.mastered == mastered)
    
    mistakes = query.order_by(GREMistake.created_at.desc()).all()
    return mistakes

@app.get("/review/today", response_model=dict)
async def get_today_reviews(db: Session = Depends(get_db)):
    """
    Fetch all mistakes where next_review_date <= now, separated by Quant and Verbal.
    """
    now = datetime.now()
    all_reviews = db.query(GREMistake).filter(
        and_(
            GREMistake.next_review_date <= now,
            GREMistake.mastered == False
        )
    ).all()
    
    quant_reviews = [mistake for mistake in all_reviews if mistake.section == "Quant"]
    verbal_reviews = [mistake for mistake in all_reviews if mistake.section == "Verbal"]
    
    return {
        "quant": quant_reviews,
        "verbal": verbal_reviews
    }

@app.post("/review/{mistake_id}/submit", response_model=ReviewResponse)
async def submit_review(
    mistake_id: int,
    review: ReviewSubmit,
    db: Session = Depends(get_db)
):
    """
    Accept a 'quality' score (1-5). 
    If score < 3, reset interval. 
    If score >= 3, increase the interval using the SM-2 logic.
    Mark as 'Mastered' if item survives 5 successful repetitions.
    Increment total_attempts and set got_correct if quality >= 4.
    """
    mistake = db.query(GREMistake).filter(GREMistake.id == mistake_id).first()
    
    if not mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")
    
    if mistake.mastered:
        raise HTTPException(status_code=400, detail="This item is already mastered")
    
    # Increment total attempts
    mistake.total_attempts = (mistake.total_attempts or 0) + 1
    
    # Set got_correct flag if quality >= 4 (Good or Easy)
    if review.quality >= 4:
        mistake.got_correct = True
    
    # Calculate next review using SM-2 algorithm
    new_interval, new_ease_factor, new_repetition_count, next_review_date = calculate_next_review(
        quality=review.quality,
        interval=mistake.interval,
        ease_factor=mistake.ease_factor,
        repetition_count=mistake.repetition_count
    )
    
    # Update mistake
    mistake.interval = new_interval
    mistake.ease_factor = new_ease_factor
    mistake.repetition_count = new_repetition_count
    mistake.next_review_date = next_review_date
    
    # Mark as mastered if 5 successful repetitions
    if new_repetition_count >= 5:
        mistake.mastered = True
    
    db.commit()
    db.refresh(mistake)
    
    return mistake

@app.get("/mistakes/{mistake_id}", response_model=GREMistakeResponse)
async def get_mistake(mistake_id: int, db: Session = Depends(get_db)):
    """Get a specific mistake by ID."""
    mistake = db.query(GREMistake).filter(GREMistake.id == mistake_id).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")
    return mistake

@app.put("/mistakes/{mistake_id}", response_model=GREMistakeResponse)
async def update_mistake(
    mistake_id: int,
    mistake: GREMistakeCreate,
    db: Session = Depends(get_db)
):
    """Update a mistake."""
    db_mistake = db.query(GREMistake).filter(GREMistake.id == mistake_id).first()
    if not db_mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")
    
    mistake_data = mistake.dict(exclude_none=False)
    # Convert empty strings to None for optional text fields
    for key in ['sub_topic', 'problem_statement_text', 'solution_text', 'what_did_i_do_wrong', 
                'what_will_i_do_next_time', 'additional_techniques', 'relevant_concept']:
        if mistake_data.get(key) == '':
            mistake_data[key] = None
    # Ensure image URL lists are lists
    if mistake_data.get("problem_statement_image_urls") is None:
        mistake_data["problem_statement_image_urls"] = []
    if mistake_data.get("solution_image_urls") is None:
        mistake_data["solution_image_urls"] = []
    
    # Update fields
    for key, value in mistake_data.items():
        setattr(db_mistake, key, value)
    
    db.commit()
    db.refresh(db_mistake)
    return db_mistake

@app.delete("/mistakes/{mistake_id}")
async def delete_mistake(mistake_id: int, db: Session = Depends(get_db)):
    """Delete a mistake."""
    mistake = db.query(GREMistake).filter(GREMistake.id == mistake_id).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")
    
    db.delete(mistake)
    db.commit()
    return {"message": "Mistake deleted successfully"}

@app.get("/mistakes/filter/options", response_model=dict)
async def get_filter_options(db: Session = Depends(get_db)):
    """Get available filter options (unique values for dropdowns)."""
    all_mistakes = db.query(GREMistake).all()
    
    sections = sorted(set(m.section for m in all_mistakes if m.section))
    topics = sorted(set(m.topic for m in all_mistakes if m.topic))
    sub_topics = sorted(set(m.sub_topic for m in all_mistakes if m.sub_topic))
    error_types = sorted(set(m.error_type for m in all_mistakes if m.error_type))
    kmf_sections = sorted(set(m.kmf_section for m in all_mistakes if m.kmf_section is not None))
    kmf_problem_sets = sorted(set(m.kmf_problem_set for m in all_mistakes if m.kmf_problem_set is not None))
    
    return {
        "sections": sections,
        "topics": topics,
        "sub_topics": sub_topics,
        "error_types": error_types,
        "kmf_sections": kmf_sections,
        "kmf_problem_sets": kmf_problem_sets
    }

@app.get("/mistakes/export/excel")
async def export_mistakes_excel(
    section: str = None,
    topic: str = None,
    sub_topic: str = None,
    error_type: str = None,
    kmf_section: int = None,
    kmf_problem_set: int = None,
    mastered: bool = None,
    db: Session = Depends(get_db)
):
    """Export mistakes to Excel format with optional filters."""
    query = db.query(GREMistake)
    
    # Apply filters
    if section:
        query = query.filter(GREMistake.section == section)
    if topic:
        query = query.filter(GREMistake.topic == topic)
    if sub_topic:
        query = query.filter(GREMistake.sub_topic == sub_topic)
    if error_type:
        query = query.filter(GREMistake.error_type == error_type)
    if kmf_section is not None:
        query = query.filter(GREMistake.kmf_section == kmf_section)
    if kmf_problem_set is not None:
        query = query.filter(GREMistake.kmf_problem_set == kmf_problem_set)
    if mastered is not None:
        query = query.filter(GREMistake.mastered == mastered)
    
    mistakes = query.all()
    
    excel_data = export_to_excel(mistakes)
    filename = f"gre_mistakes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/mistakes/export/pdf")
async def export_mistakes_pdf(
    section: str = None,
    topic: str = None,
    sub_topic: str = None,
    error_type: str = None,
    kmf_section: int = None,
    kmf_problem_set: int = None,
    mastered: bool = None,
    db: Session = Depends(get_db)
):
    """Export mistakes to PDF format with optional filters."""
    query = db.query(GREMistake)
    
    # Apply filters
    if section:
        query = query.filter(GREMistake.section == section)
    if topic:
        query = query.filter(GREMistake.topic == topic)
    if sub_topic:
        query = query.filter(GREMistake.sub_topic == sub_topic)
    if error_type:
        query = query.filter(GREMistake.error_type == error_type)
    if kmf_section is not None:
        query = query.filter(GREMistake.kmf_section == kmf_section)
    if kmf_problem_set is not None:
        query = query.filter(GREMistake.kmf_problem_set == kmf_problem_set)
    if mastered is not None:
        query = query.filter(GREMistake.mastered == mastered)
    
    mistakes = query.all()
    
    pdf_data = export_to_pdf(mistakes)
    filename = f"gre_mistakes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Exam Session Endpoints
@app.post("/exam/create", response_model=ExamSessionResponse)
async def create_exam_session(exam_config: ExamSessionCreate, db: Session = Depends(get_db)):
    """Create a new exam session with filtered mistakes. Supports multiple selections."""
    from sqlalchemy import or_
    
    # Build query based on filters - start with all mistakes
    query = db.query(GREMistake)
    
    # Apply filters only if they are provided and not empty
    filters_applied = False
    
    if exam_config.sections and len(exam_config.sections) > 0:
        query = query.filter(GREMistake.section.in_(exam_config.sections))
        filters_applied = True
    
    if exam_config.topics and len(exam_config.topics) > 0:
        query = query.filter(GREMistake.topic.in_(exam_config.topics))
        filters_applied = True
    
    if exam_config.sub_topics and len(exam_config.sub_topics) > 0:
        query = query.filter(GREMistake.sub_topic.in_(exam_config.sub_topics))
        filters_applied = True
    
    if exam_config.error_types and len(exam_config.error_types) > 0:
        query = query.filter(GREMistake.error_type.in_(exam_config.error_types))
        filters_applied = True
    
    if exam_config.kmf_sections and len(exam_config.kmf_sections) > 0:
        query = query.filter(GREMistake.kmf_section.in_(exam_config.kmf_sections))
        filters_applied = True
    
    if exam_config.kmf_problem_sets and len(exam_config.kmf_problem_sets) > 0:
        query = query.filter(GREMistake.kmf_problem_set.in_(exam_config.kmf_problem_sets))
        filters_applied = True
    
    # Get all matching mistakes (if no filters, get all mistakes)
    mistakes = query.all()
    
    if not mistakes:
        raise HTTPException(status_code=400, detail="No mistakes found matching the criteria. Try removing some filters or add more mistakes to the database.")
    
    # Store filter info as JSON for display (use first value or None)
    exam_session = ExamSession(
        section=exam_config.sections[0] if exam_config.sections and len(exam_config.sections) == 1 else None,
        topic=exam_config.topics[0] if exam_config.topics and len(exam_config.topics) == 1 else None,
        sub_topic=exam_config.sub_topics[0] if exam_config.sub_topics and len(exam_config.sub_topics) == 1 else None,
        error_type=exam_config.error_types[0] if exam_config.error_types and len(exam_config.error_types) == 1 else None,
        kmf_section=exam_config.kmf_sections[0] if exam_config.kmf_sections and len(exam_config.kmf_sections) == 1 else None,
        kmf_problem_set=exam_config.kmf_problem_sets[0] if exam_config.kmf_problem_sets and len(exam_config.kmf_problem_sets) == 1 else None,
        timer_minutes=exam_config.timer_minutes,
        total_problems=len(mistakes),
        mistake_ids=[m.id for m in mistakes],
        answers={}
    )
    
    db.add(exam_session)
    db.commit()
    db.refresh(exam_session)
    
    return exam_session

@app.post("/exam/{exam_id}/submit-answer")
async def submit_exam_answer(
    exam_id: int,
    answer: ExamAnswerSubmit,
    db: Session = Depends(get_db)
):
    """Submit an answer for a problem in the exam."""
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    if exam.completed_at:
        raise HTTPException(status_code=400, detail="Exam session already completed")
    
    # Initialize answers if needed
    if not exam.answers:
        exam.answers = {}
    
    # Check if answer was already submitted
    mistake_key = str(answer.mistake_id)
    was_already_answered = mistake_key in exam.answers
    previous_answer = exam.answers.get(mistake_key)
    
    # Update answers
    exam.answers[mistake_key] = answer.is_correct
    
    # Update counts only if this is a new answer or answer changed
    if not was_already_answered:
        # New answer
        if answer.is_correct:
            exam.correct_count += 1
        else:
            exam.incorrect_count += 1
    elif previous_answer != answer.is_correct:
        # Answer changed - adjust counts
        if previous_answer:
            exam.correct_count -= 1
            exam.incorrect_count += 1
        else:
            exam.incorrect_count -= 1
            exam.correct_count += 1
    
    db.commit()
    db.refresh(exam)
    
    return {"message": "Answer submitted", "exam": exam}

@app.post("/exam/{exam_id}/complete", response_model=ExamSessionResponse)
async def complete_exam(exam_id: int, db: Session = Depends(get_db)):
    """Mark exam session as completed."""
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    
    if exam.completed_at:
        raise HTTPException(status_code=400, detail="Exam session already completed")
    
    exam.completed_at = datetime.now()
    db.commit()
    db.refresh(exam)
    
    return exam

@app.get("/exam/history", response_model=List[ExamSessionResponse])
async def get_exam_history(db: Session = Depends(get_db)):
    """Get all completed exam sessions."""
    exams = db.query(ExamSession).filter(
        ExamSession.completed_at.isnot(None)
    ).order_by(ExamSession.completed_at.desc()).all()
    return exams

@app.get("/exam/statistics", response_model=dict)
async def get_exam_statistics(db: Session = Depends(get_db)):
    """Get exam statistics broken down by Quant and Verbal."""
    all_exams = db.query(ExamSession).filter(
        ExamSession.completed_at.isnot(None)
    ).all()
    
    # Initialize counters
    quant_total_problems = 0
    quant_correct = 0
    quant_incorrect = 0
    quant_exam_ids = set()
    
    verbal_total_problems = 0
    verbal_correct = 0
    verbal_incorrect = 0
    verbal_exam_ids = set()
    
    # Process each exam by checking individual mistakes
    for exam in all_exams:
        quant_in_exam = 0
        quant_correct_in_exam = 0
        verbal_in_exam = 0
        verbal_correct_in_exam = 0
        
        # Check each mistake in the exam
        for mistake_id in exam.mistake_ids:
            mistake = db.query(GREMistake).filter(GREMistake.id == mistake_id).first()
            if mistake:
                is_correct = exam.answers.get(str(mistake_id), False)
                if mistake.section == "Quant":
                    quant_in_exam += 1
                    quant_total_problems += 1
                    if is_correct:
                        quant_correct_in_exam += 1
                        quant_correct += 1
                    else:
                        quant_incorrect += 1
                elif mistake.section == "Verbal":
                    verbal_in_exam += 1
                    verbal_total_problems += 1
                    if is_correct:
                        verbal_correct_in_exam += 1
                        verbal_correct += 1
                    else:
                        verbal_incorrect += 1
        
        # Track exam IDs that contain each section
        if quant_in_exam > 0:
            quant_exam_ids.add(exam.id)
        if verbal_in_exam > 0:
            verbal_exam_ids.add(exam.id)
    
    # Calculate percentages
    quant_percentage = (quant_correct / quant_total_problems * 100) if quant_total_problems > 0 else 0
    verbal_percentage = (verbal_correct / verbal_total_problems * 100) if verbal_total_problems > 0 else 0
    
    # Get mistake statistics
    all_mistakes = db.query(GREMistake).all()
    quant_mistakes = [m for m in all_mistakes if m.section == "Quant"]
    verbal_mistakes = [m for m in all_mistakes if m.section == "Verbal"]
    
    quant_mastered = len([m for m in quant_mistakes if m.mastered])
    verbal_mastered = len([m for m in verbal_mistakes if m.mastered])
    
    return {
        "quant": {
            "total_problems": quant_total_problems,
            "correct": quant_correct,
            "incorrect": quant_incorrect,
            "percentage": round(quant_percentage, 1),
            "exam_count": len(quant_exam_ids),
            "total_mistakes": len(quant_mistakes),
            "mastered": quant_mastered,
            "in_progress": len(quant_mistakes) - quant_mastered
        },
        "verbal": {
            "total_problems": verbal_total_problems,
            "correct": verbal_correct,
            "incorrect": verbal_incorrect,
            "percentage": round(verbal_percentage, 1),
            "exam_count": len(verbal_exam_ids),
            "total_mistakes": len(verbal_mistakes),
            "mastered": verbal_mastered,
            "in_progress": len(verbal_mistakes) - verbal_mastered
        },
        "total_exams": len(all_exams)
    }

@app.get("/exam/{exam_id}", response_model=ExamSessionResponse)
async def get_exam_session(exam_id: int, db: Session = Depends(get_db)):
    """Get exam session details."""
    exam = db.query(ExamSession).filter(ExamSession.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam session not found")
    return exam


# Vocabulary endpoints
@app.post("/vocabulary", response_model=VocabularyResponse)
async def create_vocabulary(vocab: VocabularyCreate, db: Session = Depends(get_db)):
    """Create a new vocabulary entry."""
    # Check if word already exists
    existing = db.query(Vocabulary).filter(Vocabulary.word.ilike(vocab.word)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Vocabulary word '{vocab.word}' already exists")
    
    vocabulary = Vocabulary(
        word=vocab.word,
        set_no=vocab.set_no,
        category=vocab.category,
        meaning=vocab.meaning,
        synonym=vocab.synonym,
        sentences=vocab.sentences,
        genre=vocab.genre,
        tags=vocab.tags or [],
        source_mistake_id=vocab.source_mistake_id
    )
    
    db.add(vocabulary)
    db.commit()
    db.refresh(vocabulary)
    
    return vocabulary


@app.get("/vocabulary", response_model=List[VocabularyResponse])
async def get_vocabulary_list(
    set_no: int = None,
    category: str = None,
    genre: str = None,
    tag: str = None,
    db: Session = Depends(get_db)
):
    """Get list of vocabulary entries with optional filters."""
    query = db.query(Vocabulary)
    
    if set_no is not None:
        query = query.filter(Vocabulary.set_no == set_no)
    if category:
        query = query.filter(Vocabulary.category == category)
    if genre:
        query = query.filter(Vocabulary.genre == genre)
    if tag:
        query = query.filter(Vocabulary.tags.contains([tag]))
    
    vocabulary = query.order_by(Vocabulary.word).all()
    return vocabulary


@app.get("/vocabulary/{vocab_id}", response_model=VocabularyResponse)
async def get_vocabulary(vocab_id: int, db: Session = Depends(get_db)):
    """Get a specific vocabulary entry by ID."""
    vocabulary = db.query(Vocabulary).filter(Vocabulary.id == vocab_id).first()
    if not vocabulary:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return vocabulary


@app.put("/vocabulary/{vocab_id}", response_model=VocabularyResponse)
async def update_vocabulary(
    vocab_id: int,
    vocab_update: VocabularyUpdate,
    db: Session = Depends(get_db)
):
    """Update a vocabulary entry."""
    vocabulary = db.query(Vocabulary).filter(Vocabulary.id == vocab_id).first()
    if not vocabulary:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    
    # Update fields if provided
    if vocab_update.word is not None:
        # Check if new word already exists (excluding current entry)
        existing = db.query(Vocabulary).filter(
            Vocabulary.word.ilike(vocab_update.word),
            Vocabulary.id != vocab_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Vocabulary word '{vocab_update.word}' already exists")
        vocabulary.word = vocab_update.word
    
    if vocab_update.set_no is not None:
        vocabulary.set_no = vocab_update.set_no
    if vocab_update.category is not None:
        vocabulary.category = vocab_update.category
    if vocab_update.meaning is not None:
        vocabulary.meaning = vocab_update.meaning
    if vocab_update.synonym is not None:
        vocabulary.synonym = vocab_update.synonym
    if vocab_update.sentences is not None:
        vocabulary.sentences = vocab_update.sentences
    if vocab_update.genre is not None:
        vocabulary.genre = vocab_update.genre
    if vocab_update.tags is not None:
        vocabulary.tags = vocab_update.tags
    
    db.commit()
    db.refresh(vocabulary)
    
    return vocabulary


@app.delete("/vocabulary/{vocab_id}")
async def delete_vocabulary(vocab_id: int, db: Session = Depends(get_db)):
    """Delete a vocabulary entry."""
    vocabulary = db.query(Vocabulary).filter(Vocabulary.id == vocab_id).first()
    if not vocabulary:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    
    db.delete(vocabulary)
    db.commit()
    
    return {"message": "Vocabulary deleted successfully"}


@app.get("/vocabulary/filters/options", response_model=dict)
async def get_vocabulary_filter_options(db: Session = Depends(get_db)):
    """Get available filter options for vocabulary."""
    all_vocab = db.query(Vocabulary).all()
    
    set_nos = sorted(set(v.set_no for v in all_vocab if v.set_no is not None))
    categories = sorted(set(v.category for v in all_vocab if v.category))
    genres = sorted(set(v.genre for v in all_vocab if v.genre))
    tags = sorted(set(tag for v in all_vocab if v.tags for tag in v.tags))
    
    return {
        "set_nos": set_nos,
        "categories": categories,
        "genres": genres,
        "tags": tags
    }


@app.get("/vocabulary/export/excel")
async def export_vocabulary_excel(
    set_no: int = None,
    category: str = None,
    genre: str = None,
    tag: str = None,
    db: Session = Depends(get_db)
):
    """Export vocabulary to Excel format with optional filters."""
    query = db.query(Vocabulary)
    
    # Apply filters
    if set_no is not None:
        query = query.filter(Vocabulary.set_no == set_no)
    if category:
        query = query.filter(Vocabulary.category == category)
    if genre:
        query = query.filter(Vocabulary.genre == genre)
    if tag:
        query = query.filter(Vocabulary.tags.contains([tag]))
    
    vocabulary = query.order_by(Vocabulary.word).all()
    
    excel_data = export_vocabulary_to_excel(vocabulary)
    filename = f"vocabulary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/vocabulary/export/pdf")
async def export_vocabulary_pdf(
    set_no: int = None,
    category: str = None,
    genre: str = None,
    tag: str = None,
    db: Session = Depends(get_db)
):
    """Export vocabulary to PDF format with optional filters."""
    query = db.query(Vocabulary)
    
    # Apply filters
    if set_no is not None:
        query = query.filter(Vocabulary.set_no == set_no)
    if category:
        query = query.filter(Vocabulary.category == category)
    if genre:
        query = query.filter(Vocabulary.genre == genre)
    if tag:
        query = query.filter(Vocabulary.tags.contains([tag]))
    
    vocabulary = query.order_by(Vocabulary.word).all()
    
    pdf_data = export_vocabulary_to_pdf(vocabulary)
    filename = f"vocabulary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

