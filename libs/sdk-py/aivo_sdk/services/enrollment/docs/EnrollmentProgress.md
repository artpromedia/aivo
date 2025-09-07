# EnrollmentProgress

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enrollment_id** | **str** |  |
**progress_percentage** | **float** |  |
**time_spent_minutes** | **int** |  |
**last_accessed_at** | **datetime** |  |
**completed_modules** | **List[str]** |  | [optional]
**current_module** | **str** |  | [optional]
**assessment_scores** | [**List[EnrollmentProgressAssessmentScoresInner]**](EnrollmentProgressAssessmentScoresInner.md) |  | [optional]

## Example

```python
from aivo_sdk.models.enrollment_progress import EnrollmentProgress

# TODO update the JSON string below
json = "{}"
# create an instance of EnrollmentProgress from a JSON string
enrollment_progress_instance = EnrollmentProgress.from_json(json)
# print the JSON string representation of the object
print(EnrollmentProgress.to_json())

# convert the object into a dict
enrollment_progress_dict = enrollment_progress_instance.to_dict()
# create an instance of EnrollmentProgress from a dict
enrollment_progress_from_dict = EnrollmentProgress.from_dict(enrollment_progress_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
