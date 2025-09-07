# SubmitAssessmentRequestAnswersInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**question_id** | **str** |  |
**answer** | [**SubmitAssessmentRequestAnswersInnerAnswer**](SubmitAssessmentRequestAnswersInnerAnswer.md) |  |

## Example

```python
from aivo_sdk.models.submit_assessment_request_answers_inner import SubmitAssessmentRequestAnswersInner

# TODO update the JSON string below
json = "{}"
# create an instance of SubmitAssessmentRequestAnswersInner from a JSON string
submit_assessment_request_answers_inner_instance = SubmitAssessmentRequestAnswersInner.from_json(json)
# print the JSON string representation of the object
print(SubmitAssessmentRequestAnswersInner.to_json())

# convert the object into a dict
submit_assessment_request_answers_inner_dict = submit_assessment_request_answers_inner_instance.to_dict()
# create an instance of SubmitAssessmentRequestAnswersInner from a dict
submit_assessment_request_answers_inner_from_dict = SubmitAssessmentRequestAnswersInner.from_dict(submit_assessment_request_answers_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
