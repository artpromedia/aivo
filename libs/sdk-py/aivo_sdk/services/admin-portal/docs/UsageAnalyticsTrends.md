# UsageAnalyticsTrends

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**daily_activity** | [**List[UsageAnalyticsTrendsDailyActivityInner]**](UsageAnalyticsTrendsDailyActivityInner.md) |  | [optional]
**peak_hours** | [**List[UsageAnalyticsTrendsPeakHoursInner]**](UsageAnalyticsTrendsPeakHoursInner.md) | Learning activity by hour of day | [optional]

## Example

```python
from aivo_sdk.models.usage_analytics_trends import UsageAnalyticsTrends

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalyticsTrends from a JSON string
usage_analytics_trends_instance = UsageAnalyticsTrends.from_json(json)
# print the JSON string representation of the object
print(UsageAnalyticsTrends.to_json())

# convert the object into a dict
usage_analytics_trends_dict = usage_analytics_trends_instance.to_dict()
# create an instance of UsageAnalyticsTrends from a dict
usage_analytics_trends_from_dict = UsageAnalyticsTrends.from_dict(usage_analytics_trends_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
