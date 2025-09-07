# SubmitAssessmentRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**answers** | [**List[SubmitAssessmentRequestAnswersInner]**](SubmitAssessmentRequestAnswersInner.md) |  |
**time_spent** | **int** | Time spent in minutes | [optional]

## Example

```python
from aivo_sdk.models.submit_assessment_request import SubmitAssessmentRequest

# TODO update the JSON string below
json = "{}"
# create an instance of SubmitAssessmentRequest from a JSON string
submit_assessment_request_instance = SubmitAssessmentRequest.from_json(json)
# print the JSON string representation of the object
print(SubmitAssessmentRequest.to_json())

# convert the object into a dict
submit_assessment_request_dict = submit_assessment_request_instance.to_dict()
# create an instance of SubmitAssessmentRequest from a dict
submit_assessment_request_from_dict = SubmitAssessmentRequest.from_dict(submit_assessment_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
