# UsageAnalytics


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  | 
**range** | **str** | Time range for this analytics data | 
**total_minutes_learned** | **int** | Total learning minutes in the specified range | 
**active_learners** | [**UsageAnalyticsActiveLearners**](UsageAnalyticsActiveLearners.md) |  | 
**average_session_length** | **float** | Average learning session length in minutes | [optional] 
**completion_stats** | [**UsageAnalyticsCompletionStats**](UsageAnalyticsCompletionStats.md) |  | [optional] 
**subject_mix** | [**List[UsageAnalyticsSubjectMixInner]**](UsageAnalyticsSubjectMixInner.md) | Breakdown of learning time by subject | 
**trends** | [**UsageAnalyticsTrends**](UsageAnalyticsTrends.md) |  | 
**engagement** | [**UsageAnalyticsEngagement**](UsageAnalyticsEngagement.md) |  | [optional] 
**last_updated** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.usage_analytics import UsageAnalytics

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalytics from a JSON string
usage_analytics_instance = UsageAnalytics.from_json(json)
# print the JSON string representation of the object
print(UsageAnalytics.to_json())

# convert the object into a dict
usage_analytics_dict = usage_analytics_instance.to_dict()
# create an instance of UsageAnalytics from a dict
usage_analytics_from_dict = UsageAnalytics.from_dict(usage_analytics_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


