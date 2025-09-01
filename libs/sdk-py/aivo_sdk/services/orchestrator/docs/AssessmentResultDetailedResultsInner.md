# AssessmentResultDetailedResultsInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**question_id** | **str** |  | [optional] 
**correct** | **bool** |  | [optional] 
**points** | **float** |  | [optional] 
**feedback** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.assessment_result_detailed_results_inner import AssessmentResultDetailedResultsInner

# TODO update the JSON string below
json = "{}"
# create an instance of AssessmentResultDetailedResultsInner from a JSON string
assessment_result_detailed_results_inner_instance = AssessmentResultDetailedResultsInner.from_json(json)
# print the JSON string representation of the object
print(AssessmentResultDetailedResultsInner.to_json())

# convert the object into a dict
assessment_result_detailed_results_inner_dict = assessment_result_detailed_results_inner_instance.to_dict()
# create an instance of AssessmentResultDetailedResultsInner from a dict
assessment_result_detailed_results_inner_from_dict = AssessmentResultDetailedResultsInner.from_dict(assessment_result_detailed_results_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


