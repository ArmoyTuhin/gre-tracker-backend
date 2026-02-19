from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class GREMistake(Base):
    __tablename__ = "gre_mistakes"
    
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, nullable=False)  # "Quant" or "Verbal"
    topic = Column(String, nullable=False)  # e.g., "Geometry", "TC"
    sub_topic = Column(String, nullable=True)
    
    # KMF Fields
    kmf_section = Column(Integer, nullable=True)  # KMF Section 1-74
    kmf_problem_set = Column(Integer, nullable=True)  # Problem set 1-15
    
    # Problem Statement (can have both image and text)
    problem_statement_image_urls = Column(JSON, nullable=True, default=list)  # List of problem statement image URLs
    problem_statement_text = Column(Text, nullable=True)  # Problem statement text
    
    # Solution (can be image or text)
    solution_image_urls = Column(JSON, nullable=True, default=list)  # List of solution image URLs
    solution_text = Column(Text, nullable=True)  # Markdown/LaTeX support
    
    # Error Analysis Fields
    error_type = Column(String, nullable=False)  # "Conceptual", "Silly", "Time"
    what_did_i_do_wrong = Column(Text, nullable=True)  # What Did I do wrong?
    what_will_i_do_next_time = Column(Text, nullable=True)  # What Will I Do Next Time?
    additional_techniques = Column(Text, nullable=True)  # Additional techniques
    relevant_concept = Column(Text, nullable=True)  # Relevant Concept
    
    # SRS Data (Spaced Repetition System)
    next_review_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    interval = Column(Integer, default=0)  # Days until next review
    ease_factor = Column(Float, default=2.5)  # SM-2 ease factor
    repetition_count = Column(Integer, default=0)  # Number of successful reviews
    mastered = Column(Boolean, default=False)  # True after 5 successful repetitions
    
    # Attempt Tracking
    total_attempts = Column(Integer, default=0)  # Total number of attempts (including failed)
    got_correct = Column(Boolean, default=False)  # Flag if got correct after trying again
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, nullable=True)  # "Quant", "Verbal", or None for both
    topic = Column(String, nullable=True)
    sub_topic = Column(String, nullable=True)
    error_type = Column(String, nullable=True)
    kmf_section = Column(Integer, nullable=True)
    kmf_problem_set = Column(Integer, nullable=True)
    
    timer_minutes = Column(Integer, nullable=True)  # Timer in minutes, None for no timer
    
    total_problems = Column(Integer, nullable=False)
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Store the list of mistake IDs that were in this exam
    mistake_ids = Column(JSON, nullable=False, default=list)
    
    # Store answers: {mistake_id: correct/incorrect}
    answers = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Vocabulary(Base):
    __tablename__ = "vocabulary"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False, index=True)  # The vocabulary word
    set_no = Column(Integer, nullable=True)  # Set number
    category = Column(String, nullable=True)  # Category
    meaning = Column(Text, nullable=False)  # Meaning/definition
    synonym = Column(Text, nullable=True)  # Synonyms (comma-separated or JSON)
    sentences = Column(Text, nullable=True)  # Example sentences
    genre = Column(String, nullable=True)  # Genre
    tags = Column(JSON, nullable=True, default=list)  # Tags like "from practice set", etc.
    source_mistake_id = Column(Integer, nullable=True)  # ID of mistake this vocab came from (if from practice)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

