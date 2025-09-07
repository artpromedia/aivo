# EnrollmentProgressAssessmentScoresInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**assessment_id** | **str** |  | [optional]
**score** | **float** |  | [optional]
**completed_at** | **datetime** |  | [optional]

## Example

```python
from aivo_sdk.models.enrollment_progress_assessment_scores_inner import EnrollmentProgressAssessmentScoresInner

# TODO update the JSON string below
json = "{}"
# create an instance of EnrollmentProgressAssessmentScoresInner from a JSON string
enrollment_progress_assessment_scores_inner_instance = EnrollmentProgressAssessmentScoresInner.from_json(json)
# print the JSON string representation of the object
print(EnrollmentProgressAssessmentScoresInner.to_json())

# convert the object into a dict
enrollment_progress_assessment_scores_inner_dict = enrollment_progress_assessment_scores_inner_instance.to_dict()
# create an instance of EnrollmentProgressAssessmentScoresInner from a dict
enrollment_progress_assessment_scores_inner_from_dict = EnrollmentProgressAssessmentScoresInner.from_dict(enrollment_progress_assessment_scores_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
