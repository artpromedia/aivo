# UsageAnalyticsActiveLearners

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **int** | Number of active learners in range |
**percentage** | **float** | Percentage of total learners who were active |

## Example

```python
from aivo_sdk.models.usage_analytics_active_learners import UsageAnalyticsActiveLearners

# TODO update the JSON string below
json = "{}"
# create an instance of UsageAnalyticsActiveLearners from a JSON string
usage_analytics_active_learners_instance = UsageAnalyticsActiveLearners.from_json(json)
# print the JSON string representation of the object
print(UsageAnalyticsActiveLearners.to_json())

# convert the object into a dict
usage_analytics_active_learners_dict = usage_analytics_active_learners_instance.to_dict()
# create an instance of UsageAnalyticsActiveLearners from a dict
usage_analytics_active_learners_from_dict = UsageAnalyticsActiveLearners.from_dict(usage_analytics_active_learners_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
