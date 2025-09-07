# NamespacesOverviewRecentActivity

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespaces_created_this_week** | **int** |  | [optional]
**namespaces_created_this_month** | **int** |  | [optional]
**documents_added_this_week** | **int** |  | [optional]

## Example

```python
from aivo_sdk.models.namespaces_overview_recent_activity import NamespacesOverviewRecentActivity

# TODO update the JSON string below
json = "{}"
# create an instance of NamespacesOverviewRecentActivity from a JSON string
namespaces_overview_recent_activity_instance = NamespacesOverviewRecentActivity.from_json(json)
# print the JSON string representation of the object
print(NamespacesOverviewRecentActivity.to_json())

# convert the object into a dict
namespaces_overview_recent_activity_dict = namespaces_overview_recent_activity_instance.to_dict()
# create an instance of NamespacesOverviewRecentActivity from a dict
namespaces_overview_recent_activity_from_dict = NamespacesOverviewRecentActivity.from_dict(namespaces_overview_recent_activity_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
