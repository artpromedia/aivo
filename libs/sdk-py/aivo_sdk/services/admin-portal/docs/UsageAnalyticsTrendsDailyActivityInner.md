# UsageAnalyticsTrendsDailyActivityInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**var_date** | **date** |  | [optional] 
**minutes_learned** | **int** |  | [optional] 
**active_learners** | **int** |  | [optional] 
**sessions_started** | **int** |  | [optional] 

## Example

```python
from aivo_sdk.models.usage_analytics_trends_daily_activity_inner import UsageAnalyticsTrendsDailyActivityInner

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalyticsTrendsDailyActivityInner from a JSON string
usage_analytics_trends_daily_activity_inner_instance = UsageAnalyticsTrendsDailyActivityInner.from_json(json)
# print the JSON string representation of the object
print(UsageAnalyticsTrendsDailyActivityInner.to_json())

# convert the object into a dict
usage_analytics_trends_daily_activity_inner_dict = usage_analytics_trends_daily_activity_inner_instance.to_dict()
# create an instance of UsageAnalyticsTrendsDailyActivityInner from a dict
usage_analytics_trends_daily_activity_inner_from_dict = UsageAnalyticsTrendsDailyActivityInner.from_dict(usage_analytics_trends_daily_activity_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


