# UsageAnalyticsCompletionStats

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**courses_completed** | **int** |  | [optional]
**modules_completed** | **int** |  | [optional]
**assessments_passed** | **int** |  | [optional]

## Example

```python
from aivo_sdk.models.usage_analytics_completion_stats import UsageAnalyticsCompletionStats

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalyticsCompletionStats from a JSON string
usage_analytics_completion_stats_instance = UsageAnalyticsCompletionStats.from_json(json)
# print the JSON string representation of the object
print(UsageAnalyticsCompletionStats.to_json())

# convert the object into a dict
usage_analytics_completion_stats_dict = usage_analytics_completion_stats_instance.to_dict()
# create an instance of UsageAnalyticsCompletionStats from a dict
usage_analytics_completion_stats_from_dict = UsageAnalyticsCompletionStats.from_dict(usage_analytics_completion_stats_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
