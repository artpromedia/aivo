"""
CALPADS (California) compliance exporter.
Generates state-format CSV exports for California reporting requirements.
"""

import csv
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ExportJob


class CALPADSExporter:
    """CALPADS compliance data exporter for California."""

    # CALPADS CSV headers broken across multiple lines for lint hygiene
    CALPADS_SENR_HEADERS = [
        "academic_year",
        "district_code",
        "school_code",
        "student_id",
        "local_student_id",
        "student_legal_first_name",
        "student_legal_middle_name",
        "student_legal_last_name",
        "student_name_suffix",
        "student_birth_date",
        "student_gender",
        "student_birth_state_province",
        "student_birth_country",
        "student_primary_language",
        "student_correspondence_language",
        "parent_guardian_first_name",
        "parent_guardian_last_name",
        "student_address",
        "student_city",
        "student_state",
        "student_zip_code",
        "student_phone_number",
        "grade_level",
        "enrollment_start_date",
        "enrollment_end_date",
        "enrollment_status",
        "school_of_attendance",
        "resident_district",
        "serving_district",
        "educational_program_code",
        "funding_source",
        "ethnic_code",
        "race_code_1",
        "race_code_2",
        "race_code_3",
        "race_code_4",
        "race_code_5",
        "english_language_acquisition_status",
        "english_language_acquisition_status_start_date",
        "primary_disability_code",
        "secondary_disability_code",
        "section_504_plan_code",
        "title_i_part_a_program_type",
        "migrant_education_program_type",
        "homeless_program_type",
        "foster_youth_status",
        "military_student_identifier",
        "student_meal_program_direct_certification",
        "economic_disadvantaged_status",
    ]

    CALPADS_SASS_HEADERS = [
        "academic_year",
        "district_code",
        "school_code",
        "student_id",
        "test_id",
        "test_type",
        "administration_condition",
        "completion_status",
        "overall_scale_score",
        "overall_performance_level",
        "claim_1_scale_score",
        "claim_1_performance_level",
        "claim_2_scale_score",
        "claim_2_performance_level",
        "claim_3_scale_score",
        "claim_3_performance_level",
        "claim_4_scale_score",
        "claim_4_performance_level",
        "raw_score_claim_1",
        "raw_score_claim_2",
        "raw_score_claim_3",
        "raw_score_claim_4",
        "total_raw_score",
        "standard_error_measurement",
        "accommodations_linguistic_supports",
        "accommodations_accessibility_supports",
    ]

    CALPADS_SDIS_HEADERS = [
        "academic_year",
        "district_code",
        "school_code",
        "student_id",
        "incident_id",
        "incident_date",
        "incident_time",
        "incident_location",
        "incident_type",
        "incident_resulted_in_injury",
        "weapon_involved",
        "weapon_type",
        "related_to_disability",
        "disciplinary_action_taken",
        "discipline_start_date",
        "discipline_end_date",
        "discipline_duration_days",
        "alternative_education_placement",
        "removal_reason",
        "continuing_services",
        "notification_parent_guardian",
        "notification_law_enforcement",
        "manifestation_meeting_held",
        "manifestation_determination",
        "interim_alternative_educational_setting",
    ]

    def __init__(self, db_session: AsyncSession):
        """
        Initialize CALPADS exporter.

        Args:
            db_session: Async database session
        """
        self.db_session = db_session

    async def export_senr_data(
        self,
        export_job: ExportJob,
        output_path: Path,
        school_year: str,
        district_code: str | None = None,
        school_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Export Student Enrollment (SENR) data in CALPADS format.

        Args:
            export_job: Export job instance
            output_path: Path for output CSV file
            school_year: Academic year (e.g., "2023-24")
            district_code: Optional district filter
            school_code: Optional school filter

        Returns:
            Export statistics
        """
        # Query enrollment data
        senr_data = await self._query_senr_data(school_year, district_code, school_code)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV with proper header formatting
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=self.CALPADS_SENR_HEADERS,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()

            processed = 0
            for enrollment in senr_data:
                writer.writerow(self._transform_senr_record(enrollment))
                processed += 1

                # Update progress periodically
                if processed % 1000 == 0:
                    progress = min(100, int((processed / len(senr_data)) * 100))
                    await self._update_job_progress(export_job, progress, processed)

        return {
            "total_records": len(senr_data),
            "processed_records": processed,
            "file_size": output_path.stat().st_size,
            "export_type": "student_enrollment_senr",
        }

    async def export_sass_data(
        self,
        export_job: ExportJob,
        output_path: Path,
        school_year: str,
        test_type: str | None = None,
        district_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Export Student Assessment (SASS) data in CALPADS format.

        Args:
            export_job: Export job instance
            output_path: Path for output CSV file
            school_year: Academic year
            test_type: Optional test type filter (SBAC, CAST, etc.)
            district_code: Optional district filter

        Returns:
            Export statistics
        """
        # Query assessment data
        sass_data = await self._query_sass_data(school_year, test_type, district_code)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV with proper header formatting
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=self.CALPADS_SASS_HEADERS,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()

            processed = 0
            for assessment in sass_data:
                writer.writerow(self._transform_sass_record(assessment))
                processed += 1

                # Update progress periodically
                if processed % 1000 == 0:
                    progress = min(100, int((processed / len(sass_data)) * 100))
                    await self._update_job_progress(export_job, progress, processed)

        return {
            "total_records": len(sass_data),
            "processed_records": processed,
            "file_size": output_path.stat().st_size,
            "export_type": "student_assessment_sass",
        }

    async def export_sdis_data(
        self,
        export_job: ExportJob,
        output_path: Path,
        school_year: str,
        district_code: str | None = None,
        school_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Export Student Discipline (SDIS) data in CALPADS format.

        Args:
            export_job: Export job instance
            output_path: Path for output CSV file
            school_year: Academic year
            district_code: Optional district filter
            school_code: Optional school filter

        Returns:
            Export statistics
        """
        # Query discipline data
        sdis_data = await self._query_sdis_data(school_year, district_code, school_code)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV with proper header formatting
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=self.CALPADS_SDIS_HEADERS,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()

            processed = 0
            for discipline in sdis_data:
                writer.writerow(self._transform_sdis_record(discipline))
                processed += 1

                # Update progress periodically
                if processed % 1000 == 0:
                    progress = min(100, int((processed / len(sdis_data)) * 100))
                    await self._update_job_progress(export_job, progress, processed)

        return {
            "total_records": len(sdis_data),
            "processed_records": processed,
            "file_size": output_path.stat().st_size,
            "export_type": "student_discipline_sdis",
        }

    async def _query_senr_data(
        self,
        school_year: str,
        district_code: str | None = None,
        school_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query student enrollment data from database."""
        # Placeholder - implement actual database query
        # This would typically join students, enrollments, demographics, etc.
        return [
            {
                "academic_year": school_year,
                "district_code": district_code or "19647330000000",
                "school_code": school_code or "1964733001234",
                "student_id": f"CA{i:012d}",
                "local_student_id": f"LOC{i:08d}",
                "student_legal_first_name": f"Student{i}",
                "student_legal_middle_name": "M",
                "student_legal_last_name": f"Last{i}",
                "student_name_suffix": "",
                "student_birth_date": "01/01/2010",
                "student_gender": "M" if i % 2 == 0 else "F",
                "student_birth_state_province": "CA",
                "student_birth_country": "US",
                "student_primary_language": "00" if i % 3 == 0 else "01",
                "student_correspondence_language": "00",
                "parent_guardian_first_name": f"Parent{i}",
                "parent_guardian_last_name": f"Last{i}",
                "student_address": f"{i} Main St",
                "student_city": "Los Angeles",
                "student_state": "CA",
                "student_zip_code": "90210",
                "student_phone_number": f"555{i:07d}",
                "grade_level": "05",
                "enrollment_start_date": "08/15/2023",
                "enrollment_end_date": "",
                "enrollment_status": "1",
                "school_of_attendance": school_code or "1964733001234",
                "resident_district": district_code or "19647330000000",
                "serving_district": district_code or "19647330000000",
                "educational_program_code": "000",
                "funding_source": "1",
                "ethnic_code": "4" if i % 5 == 0 else "7",
                "race_code_1": "5",
                "race_code_2": "",
                "race_code_3": "",
                "race_code_4": "",
                "race_code_5": "",
                "english_language_acquisition_status": "EO",
                "english_language_acquisition_status_start_date": "",
                "primary_disability_code": "",
                "secondary_disability_code": "",
                "section_504_plan_code": "N",
                "title_i_part_a_program_type": "1",
                "migrant_education_program_type": "N",
                "homeless_program_type": "N",
                "foster_youth_status": "N",
                "military_student_identifier": "N",
                "student_meal_program_direct_certification": "N",
                "economic_disadvantaged_status": "Y" if i % 3 == 0 else "N",
            }
            for i in range(1500)  # Simulated data
        ]

    async def _query_sass_data(
        self,
        school_year: str,
        test_type: str | None = None,
        district_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query student assessment data from database."""
        # Placeholder - implement actual database query
        return [
            {
                "academic_year": school_year,
                "district_code": district_code or "19647330000000",
                "school_code": "1964733001234",
                "student_id": f"CA{i:012d}",
                "test_id": f"SBAC{i:010d}",
                "test_type": test_type or "SBAC",
                "administration_condition": "SD",
                "completion_status": "C",
                "overall_scale_score": str(2450 + (i % 400)),
                "overall_performance_level": str(2 + (i % 3)),
                "claim_1_scale_score": str(2420 + (i % 100)),
                "claim_1_performance_level": str(2 + (i % 3)),
                "claim_2_scale_score": str(2430 + (i % 100)),
                "claim_2_performance_level": str(2 + (i % 3)),
                "claim_3_scale_score": str(2440 + (i % 100)),
                "claim_3_performance_level": str(2 + (i % 3)),
                "claim_4_scale_score": str(2450 + (i % 100)),
                "claim_4_performance_level": str(2 + (i % 3)),
                "raw_score_claim_1": str(15 + (i % 10)),
                "raw_score_claim_2": str(12 + (i % 8)),
                "raw_score_claim_3": str(18 + (i % 12)),
                "raw_score_claim_4": str(20 + (i % 15)),
                "total_raw_score": str(65 + (i % 45)),
                "standard_error_measurement": "15",
                "accommodations_linguistic_supports": "",
                "accommodations_accessibility_supports": "",
            }
            for i in range(1200)  # Simulated data
        ]

    async def _query_sdis_data(
        self,
        school_year: str,
        district_code: str | None = None,
        school_code: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query student discipline data from database."""
        # Placeholder - implement actual database query
        return [
            {
                "academic_year": school_year,
                "district_code": district_code or "19647330000000",
                "school_code": school_code or "1964733001234",
                "student_id": f"CA{i:012d}",
                "incident_id": f"INC{i:08d}",
                "incident_date": "03/15/2024",
                "incident_time": "10:30",
                "incident_location": "CLASSROOM",
                "incident_type": "DEFIANCE",
                "incident_resulted_in_injury": "N",
                "weapon_involved": "N",
                "weapon_type": "",
                "related_to_disability": "N",
                "disciplinary_action_taken": "SUSPENSION",
                "discipline_start_date": "03/16/2024",
                "discipline_end_date": "03/18/2024",
                "discipline_duration_days": "3",
                "alternative_education_placement": "N",
                "removal_reason": "",
                "continuing_services": "Y",
                "notification_parent_guardian": "Y",
                "notification_law_enforcement": "N",
                "manifestation_meeting_held": "N",
                "manifestation_determination": "",
                "interim_alternative_educational_setting": "N",
            }
            for i in range(75)  # Simulated data
        ]

    def _transform_senr_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Transform enrollment record to CALPADS SENR format."""
        transformed = record.copy()

        # Apply CALPADS-specific transformations
        if "student_birth_date" in transformed and transformed["student_birth_date"]:
            # Ensure date format is MM/DD/YYYY for CALPADS
            birth_date = str(transformed["student_birth_date"])
            if "-" in birth_date:  # Convert from YYYY-MM-DD to MM/DD/YYYY
                parts = birth_date[:10].split("-")
                if len(parts) == 3:
                    transformed["student_birth_date"] = f"{parts[1]}/{parts[2]}/{parts[0]}"

        return transformed

    def _transform_sass_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Transform assessment record to CALPADS SASS format."""
        transformed = record.copy()

        # Apply assessment-specific transformations
        # CALPADS has specific scale score ranges and performance levels
        return transformed

    def _transform_sdis_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Transform discipline record to CALPADS SDIS format."""
        transformed = record.copy()

        # Apply discipline-specific transformations
        if "incident_date" in transformed and transformed["incident_date"]:
            # Ensure date format is MM/DD/YYYY for CALPADS
            incident_date = str(transformed["incident_date"])
            if "-" in incident_date:  # Convert from YYYY-MM-DD to MM/DD/YYYY
                parts = incident_date[:10].split("-")
                if len(parts) == 3:
                    transformed["incident_date"] = f"{parts[1]}/{parts[2]}/{parts[0]}"

        return transformed

    async def _update_job_progress(
        self,
        export_job: ExportJob,
        progress_percentage: int,
        processed_records: int,
    ) -> None:
        """Update export job progress."""
        export_job.progress_percentage = progress_percentage
        export_job.processed_records = processed_records

        # Commit progress update
        await self.db_session.commit()

    async def validate_calpads_data(
        self,
        data_type: str,
        school_year: str,
        district_code: str | None = None,
    ) -> dict[str, Any]:
        """
        Validate CALPADS data before export.

        Args:
            data_type: Type of data to validate (senr, sass, sdis)
            school_year: Academic year
            district_code: Optional district filter

        Returns:
            Validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "record_counts": {},
        }

        if data_type == "senr":
            # Validate SENR enrollment data
            senr_data = await self._query_senr_data(school_year, district_code)
            validation_results["record_counts"]["enrollments"] = len(senr_data)

            # Check for required CALPADS fields
            for i, enrollment in enumerate(senr_data[:100]):  # Sample validation
                if not enrollment.get("student_id"):
                    validation_results["errors"].append(f"Row {i+1}: Missing student_id")
                    validation_results["is_valid"] = False

                if not enrollment.get("district_code"):
                    validation_results["errors"].append(f"Row {i+1}: Missing district_code")
                    validation_results["is_valid"] = False

        elif data_type == "sass":
            # Validate SASS assessment data
            sass_data = await self._query_sass_data(school_year, None, district_code)
            validation_results["record_counts"]["assessments"] = len(sass_data)

        elif data_type == "sdis":
            # Validate SDIS discipline data
            sdis_data = await self._query_sdis_data(school_year, district_code)
            validation_results["record_counts"]["discipline_incidents"] = len(sdis_data)

        return validation_results
