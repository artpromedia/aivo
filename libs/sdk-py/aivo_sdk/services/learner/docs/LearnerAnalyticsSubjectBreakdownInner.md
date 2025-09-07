# LearnerAnalyticsSubjectBreakdownInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** |  | [optional]
**minutes_learned** | **int** |  | [optional]
**percentage** | **float** |  | [optional]

## Example

```python
from aivo_sdk.models.learner_analytics_subject_breakdown_inner import LearnerAnalyticsSubjectBreakdownInner

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerAnalyticsSubjectBreakdownInner from a JSON string
learner_analytics_subject_breakdown_inner_instance = LearnerAnalyticsSubjectBreakdownInner.from_json(json)
# print the JSON string representation of the object
print(LearnerAnalyticsSubjectBreakdownInner.to_json())

# convert the object into a dict
learner_analytics_subject_breakdown_inner_dict = learner_analytics_subject_breakdown_inner_instance.to_dict()
# create an instance of LearnerAnalyticsSubjectBreakdownInner from a dict
learner_analytics_subject_breakdown_inner_from_dict = LearnerAnalyticsSubjectBreakdownInner.from_dict(learner_analytics_subject_breakdown_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
