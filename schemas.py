from pydantic import BaseModel, Field
from typing import List

class DayPlan(BaseModel):
    day: int = Field(..., description="The study day number.")
    focus_topic: str = Field(..., description="The main topic to be covered on this day.")
    tasks: List[str] = Field(..., description="A list of specific, actionable study tasks for the day.")

# NEW SCHEMA for questions and their answers
class QuestionAnswer(BaseModel):
    question: str = Field(..., description="The question text.")
    answer: str = Field(..., description="The comprehensive answer to the question, based on provided notes.")

class StudyGuide(BaseModel):
    study_guide_title: str = Field(..., description="A catchy and relevant title for the study guide.")
    total_days: int = Field(..., description="The total number of days in the study plan.")
    key_terms: List[str] = Field(..., description="5-7 essential key terms extracted from the material.")
    high_priority_practice: List[str] = Field(..., description="2-3 high-priority practice questions/exercises derived from exam analysis.")
    study_plan: List[DayPlan] = Field(..., description="The day-by-day breakdown of the study plan.")
    
    # Updated to use QuestionAnswer schema for structured answers
    short_answer_questions: List[QuestionAnswer] = Field(..., description="A list of 8 predicted short-answer questions (SAQs) and their answers.")
    long_answer_questions: List[QuestionAnswer] = Field(..., description="A list of 4 predicted long-answer or essay questions (LAQs) and their answers.")