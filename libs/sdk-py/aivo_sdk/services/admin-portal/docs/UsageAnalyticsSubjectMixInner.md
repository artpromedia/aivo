# UsageAnalyticsSubjectMixInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**subject** | **str** | Subject or course category |
**minutes_learned** | **int** | Minutes learned in this subject |
**percentage** | **float** | Percentage of total learning time |
**learner_count** | **int** | Number of learners who studied this subject |

## Example

```python
from aivo_sdk.models.usage_analytics_subject_mix_inner import UsageAnalyticsSubjectMixInner

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalyticsSubjectMixInner from a JSON string
usage_analytics_subject_mix_inner_instance = UsageAnalyticsSubjectMixInner.from_json(json)
# print the JSON string representation of the object
print(UsageAnalyticsSubjectMixInner.to_json())

# convert the object into a dict
usage_analytics_subject_mix_inner_dict = usage_analytics_subject_mix_inner_instance.to_dict()
# create an instance of UsageAnalyticsSubjectMixInner from a dict
usage_analytics_subject_mix_inner_from_dict = UsageAnalyticsSubjectMixInner.from_dict(usage_analytics_subject_mix_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
