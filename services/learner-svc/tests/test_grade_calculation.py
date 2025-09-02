"""
Tests for grade calculation service.
"""
import pytest
from datetime import date
from app.services import GradeCalculatorService


class TestGradeCalculatorService:
    """Test grade calculation logic."""
    
    def test_kindergarten_age_calculation(self):
        """Test kindergarten age calculation (5 years old by Sept 1)."""
        calculator = GradeCalculatorService()
        
        # Child turns 5 on Aug 15, 2023 - should be in Kindergarten (grade 0)
        dob = date(2018, 8, 15)
        reference_date = date(2023, 9, 15)  # September 15, 2023
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 0
        
        # Child turns 5 on Sept 2, 2023 - just missed cutoff, pre-K (grade -1) 
        dob = date(2018, 9, 2)
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == -1
    
    def test_first_grade_calculation(self):
        """Test first grade calculation (6 years old by Sept 1)."""
        calculator = GradeCalculatorService()
        
        # Child turns 6 on July 10, 2023 - should be in 1st grade
        dob = date(2017, 7, 10)
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 1
    
    def test_middle_school_calculation(self):
        """Test middle school grade calculation."""
        calculator = GradeCalculatorService()
        
        # Child turns 12 on June 1, 2023 - should be in 7th grade
        dob = date(2011, 6, 1)
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 7
    
    def test_high_school_calculation(self):
        """Test high school grade calculation."""
        calculator = GradeCalculatorService()
        
        # Child turns 17 on March 20, 2023 - should be in 12th grade
        dob = date(2006, 3, 20)
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 12
    
    def test_cutoff_date_edge_cases(self):
        """Test edge cases around the September 1st cutoff."""
        calculator = GradeCalculatorService()
        
        # Child born on Sept 1 exactly - should make the cutoff
        dob = date(2018, 9, 1)
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 0  # Kindergarten
        
        # Child born on Aug 31 - should make the cutoff
        dob = date(2018, 8, 31)
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 0  # Kindergarten
    
    def test_before_school_year_start(self):
        """Test calculation when reference date is before school year start."""
        calculator = GradeCalculatorService()
        
        # Reference date in July, child turns 5 in August - should be Kindergarten
        dob = date(2018, 8, 15)
        reference_date = date(2023, 7, 15)  # July 15, 2023
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 0  # Kindergarten
    
    def test_grade_bounds(self):
        """Test that grades are bounded correctly."""
        calculator = GradeCalculatorService()
        
        # Very young child - should be clamped to pre-K
        dob = date(2022, 6, 1)  # Very young
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == -1  # Pre-K (minimum)
        
        # Very old student - should be clamped to 12th grade
        dob = date(2000, 6, 1)  # 23 years old
        reference_date = date(2023, 9, 15)
        grade = calculator.calculate_grade_from_dob(dob, reference_date)
        assert grade == 12  # 12th grade (maximum)
    
    def test_typical_scenarios(self):
        """Test typical real-world scenarios."""
        calculator = GradeCalculatorService()
        reference_date = date(2023, 10, 15)  # October 2023
        
        test_cases = [
            (date(2015, 3, 10), 3),   # 8 years old → 3rd grade
            (date(2014, 11, 5), 4),   # 9 years old → 4th grade
            (date(2013, 7, 20), 5),   # 10 years old → 5th grade
            (date(2012, 12, 1), 5),   # 10 years old → 5th grade (birthday after Sept 1)
            (date(2011, 4, 15), 7),   # 12 years old → 7th grade
            (date(2009, 8, 30), 9),   # 14 years old → 9th grade
            (date(2007, 1, 10), 11),  # 16 years old → 11th grade
        ]
        
        for dob, expected_grade in test_cases:
            actual_grade = calculator.calculate_grade_from_dob(dob, reference_date)
            assert actual_grade == expected_grade, f"DOB {dob} should be grade {expected_grade}, got {actual_grade}"
