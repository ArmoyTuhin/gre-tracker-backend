"""
SM-2 Spaced Repetition Algorithm Implementation
Based on SuperMemo 2 algorithm for calculating next review dates.
"""
from datetime import datetime, timedelta
from typing import Tuple

def calculate_next_review(
    quality: int,
    interval: int,
    ease_factor: float,
    repetition_count: int
) -> Tuple[int, float, int, datetime]:
    """
    Calculate next review date using SM-2 algorithm.
    
    Args:
        quality: User-reported difficulty/quality score (1-5)
                1 = Complete blackout
                2 = Incorrect response, but remembered
                3 = Correct response with difficulty
                4 = Correct response after hesitation
                5 = Perfect response
        interval: Current interval in days
        ease_factor: Current ease factor (default 2.5)
        repetition_count: Current number of successful repetitions
    
    Returns:
        Tuple of (new_interval, new_ease_factor, new_repetition_count, next_review_date)
    """
    if quality < 3:
        # If quality < 3, reset the interval
        new_interval = 1
        new_repetition_count = 0
    else:
        # Calculate new ease factor
        new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure ease factor doesn't go below 1.3
        if new_ease_factor < 1.3:
            new_ease_factor = 1.3
        
        # Calculate new interval
        if repetition_count == 0:
            new_interval = 1
        elif repetition_count == 1:
            new_interval = 6
        else:
            new_interval = int(interval * new_ease_factor)
        
        new_repetition_count = repetition_count + 1
    
    # Calculate next review date
    next_review_date = datetime.now() + timedelta(days=new_interval)
    
    return new_interval, new_ease_factor, new_repetition_count, next_review_date

