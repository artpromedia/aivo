# UsageAnalyticsEngagement

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**average_streak_days** | **float** |  | [optional]
**return_rate** | **float** | Percentage of learners who return within 7 days | [optional]

## Example

```python
from aivo_sdk.models.usage_analytics_engagement import UsageAnalyticsEngagement

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalyticsEngagement from a JSON string
usage_analytics_engagement_instance = UsageAnalyticsEngagement.from_json(json)
# print the JSON string representation of the object
print(UsageAnalyticsEngagement.to_json())

# convert the object into a dict
usage_analytics_engagement_dict = usage_analytics_engagement_instance.to_dict()
# create an instance of UsageAnalyticsEngagement from a dict
usage_analytics_engagement_from_dict = UsageAnalyticsEngagement.from_dict(usage_analytics_engagement_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
