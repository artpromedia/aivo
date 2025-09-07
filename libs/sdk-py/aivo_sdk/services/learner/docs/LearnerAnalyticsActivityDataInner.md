# LearnerAnalyticsActivityDataInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_date** | **date** |  | [optional]
**minutes_learned** | **int** |  | [optional]
**sessions_count** | **int** |  | [optional]

## Example

```python
from aivo_sdk.models.learner_analytics_activity_data_inner import LearnerAnalyticsActivityDataInner

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerAnalyticsActivityDataInner from a JSON string
learner_analytics_activity_data_inner_instance = LearnerAnalyticsActivityDataInner.from_json(json)
# print the JSON string representation of the object
print(LearnerAnalyticsActivityDataInner.to_json())

# convert the object into a dict
learner_analytics_activity_data_inner_dict = learner_analytics_activity_data_inner_instance.to_dict()
# create an instance of LearnerAnalyticsActivityDataInner from a dict
learner_analytics_activity_data_inner_from_dict = LearnerAnalyticsActivityDataInner.from_dict(learner_analytics_activity_data_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
