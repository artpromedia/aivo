# LearnerAnalytics

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**learner_id** | **str** |  |
**range** | **str** |  |
**total_learning_time** | **int** | Total learning time in minutes |
**completion_rate** | **float** |  |
**streak_days** | **int** |  |
**courses_started** | **int** |  | [optional]
**courses_completed** | **int** |  | [optional]
**average_session_length** | **int** | Average session length in minutes | [optional]
**activity_data** | [**List[LearnerAnalyticsActivityDataInner]**](LearnerAnalyticsActivityDataInner.md) |  |
**subject_breakdown** | [**List[LearnerAnalyticsSubjectBreakdownInner]**](LearnerAnalyticsSubjectBreakdownInner.md) |  | [optional]

## Example

```python
from aivo_sdk.models.learner_analytics import LearnerAnalytics

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerAnalytics from a JSON string
learner_analytics_instance = LearnerAnalytics.from_json(json)
# print the JSON string representation of the object
print(LearnerAnalytics.to_json())

# convert the object into a dict
learner_analytics_dict = learner_analytics_instance.to_dict()
# create an instance of LearnerAnalytics from a dict
learner_analytics_from_dict = LearnerAnalytics.from_dict(learner_analytics_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
