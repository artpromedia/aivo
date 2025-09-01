# AssessmentResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**assessment_id** | **str** |  | 
**learner_id** | **str** |  | 
**score** | **float** |  | 
**max_score** | **float** |  | 
**percentage** | **float** |  | [optional] 
**passed** | **bool** |  | 
**time_spent** | **int** | Time spent in minutes | [optional] 
**attempt** | **int** |  | [optional] 
**feedback** | **str** |  | [optional] 
**detailed_results** | [**List[AssessmentResultDetailedResultsInner]**](AssessmentResultDetailedResultsInner.md) |  | [optional] 
**submitted_at** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.assessment_result import AssessmentResult

# TODO update the JSON string below
json = "{}"
# create an instance of AssessmentResult from a JSON string
assessment_result_instance = AssessmentResult.from_json(json)
# print the JSON string representation of the object
print(AssessmentResult.to_json())

# convert the object into a dict
assessment_result_dict = assessment_result_instance.to_dict()
# create an instance of AssessmentResult from a dict
assessment_result_from_dict = AssessmentResult.from_dict(assessment_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


