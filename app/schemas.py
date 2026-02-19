from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Union

class GREMistakeCreate(BaseModel):
    section: str = Field(..., description="Section: 'Quant' or 'Verbal'")
    topic: str = Field(..., description="Topic e.g., 'Geometry', 'TC'")
    sub_topic: Optional[str] = None
    
    # KMF Fields - accept int, str, or None
    kmf_section: Optional[int] = Field(None, description="KMF Section (1-74)")
    kmf_problem_set: Optional[int] = Field(None, description="KMF Problem Set (1-15)")
    
    # Problem Statement
    problem_statement_image_urls: Optional[List[str]] = Field(default_factory=list, description="List of problem statement image URLs")
    problem_statement_text: Optional[str] = None
    
    # Solution (can be image or text)
    solution_image_urls: Optional[List[str]] = Field(default_factory=list, description="List of solution image URLs")
    solution_text: Optional[str] = None
    
    # Error Analysis Fields
    error_type: str = Field(..., description="Error type: 'Conceptual', 'Silly', or 'Time'")
    what_did_i_do_wrong: Optional[str] = None
    what_will_i_do_next_time: Optional[str] = None
    additional_techniques: Optional[str] = None
    relevant_concept: Optional[str] = None
    
    @field_validator('kmf_section', 'kmf_problem_set', mode='before')
    @classmethod
    def convert_empty_to_none(cls, v):
        if v == '' or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v
    
    @field_validator('kmf_section', mode='after')
    @classmethod
    def validate_kmf_section(cls, v):
        if v is not None and not (1 <= v <= 74):
            raise ValueError('KMF Section must be between 1 and 74')
        return v
    
    @field_validator('kmf_problem_set', mode='after')
    @classmethod
    def validate_kmf_problem_set(cls, v):
        if v is not None and not (1 <= v <= 15):
            raise ValueError('KMF Problem Set must be between 1 and 15')
        return v

class GREMistakeResponse(BaseModel):
    id: int
    section: str
    topic: str
    sub_topic: Optional[str]
    kmf_section: Optional[int]
    kmf_problem_set: Optional[int]
    problem_statement_image_urls: Optional[List[str]]
    problem_statement_text: Optional[str]
    solution_image_urls: Optional[List[str]]
    solution_text: Optional[str]
    error_type: str
    what_did_i_do_wrong: Optional[str]
    what_will_i_do_next_time: Optional[str]
    additional_techniques: Optional[str]
    relevant_concept: Optional[str]
    next_review_date: datetime
    interval: int
    ease_factor: float
    repetition_count: int
    mastered: bool
    total_attempts: int
    got_correct: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ReviewSubmit(BaseModel):
    quality: int = Field(..., ge=1, le=5, description="Quality score from 1-5")

class ReviewResponse(BaseModel):
    id: int
    section: str
    topic: str
    sub_topic: Optional[str]
    kmf_section: Optional[int]
    kmf_problem_set: Optional[int]
    problem_statement_image_urls: Optional[List[str]]
    problem_statement_text: Optional[str]
    solution_image_urls: Optional[List[str]]
    solution_text: Optional[str]
    error_type: str
    what_did_i_do_wrong: Optional[str]
    what_will_i_do_next_time: Optional[str]
    additional_techniques: Optional[str]
    relevant_concept: Optional[str]
    next_review_date: datetime
    interval: int
    ease_factor: float
    repetition_count: int
    mastered: bool
    total_attempts: int
    got_correct: bool
    
    class Config:
        from_attributes = True

class MistakeFilter(BaseModel):
    section: Optional[str] = None
    topic: Optional[str] = None
    sub_topic: Optional[str] = None
    error_type: Optional[str] = None
    kmf_section: Optional[int] = None
    kmf_problem_set: Optional[int] = None
    mastered: Optional[bool] = None


class ExamSessionCreate(BaseModel):
    sections: Optional[List[str]] = None  # Multiple sections
    topics: Optional[List[str]] = None  # Multiple topics
    sub_topics: Optional[List[str]] = None  # Multiple sub-topics
    error_types: Optional[List[str]] = None  # Multiple error types
    kmf_sections: Optional[List[int]] = None  # Multiple KMF sections
    kmf_problem_sets: Optional[List[int]] = None  # Multiple problem sets
    timer_minutes: Optional[int] = Field(None, ge=1, description="Timer in minutes")


class ExamAnswerSubmit(BaseModel):
    mistake_id: int
    is_correct: bool


class ExamSessionResponse(BaseModel):
    id: int
    section: Optional[str]
    topic: Optional[str]
    sub_topic: Optional[str]
    error_type: Optional[str]
    kmf_section: Optional[int]
    kmf_problem_set: Optional[int]
    timer_minutes: Optional[int]
    total_problems: int
    correct_count: int
    incorrect_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    mistake_ids: List[int]
    answers: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class VocabularyCreate(BaseModel):
    word: str = Field(..., description="The vocabulary word")
    set_no: Optional[int] = Field(None, description="Set number")
    category: Optional[str] = Field(None, description="Category")
    meaning: str = Field(..., description="Meaning/definition")
    synonym: Optional[str] = Field(None, description="Synonyms")
    sentences: Optional[str] = Field(None, description="Example sentences")
    genre: Optional[str] = Field(None, description="Genre")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags")
    source_mistake_id: Optional[int] = Field(None, description="ID of mistake this vocab came from")


class VocabularyUpdate(BaseModel):
    word: Optional[str] = None
    set_no: Optional[int] = None
    category: Optional[str] = None
    meaning: Optional[str] = None
    synonym: Optional[str] = None
    sentences: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[List[str]] = None


class VocabularyResponse(BaseModel):
    id: int
    word: str
    set_no: Optional[int]
    category: Optional[str]
    meaning: str
    synonym: Optional[str]
    sentences: Optional[str]
    genre: Optional[str]
    tags: Optional[List[str]]
    source_mistake_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

