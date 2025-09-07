# NamespacesOverview

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  |
**total_namespaces** | **int** | Total number of learner private-brain namespaces |
**status_counts** | [**NamespacesOverviewStatusCounts**](NamespacesOverviewStatusCounts.md) |  |
**storage_stats** | [**NamespacesOverviewStorageStats**](NamespacesOverviewStorageStats.md) |  | [optional]
**top_namespaces** | [**List[NamespacesOverviewTopNamespacesInner]**](NamespacesOverviewTopNamespacesInner.md) | Most active or largest namespaces |
**recent_activity** | [**NamespacesOverviewRecentActivity**](NamespacesOverviewRecentActivity.md) |  | [optional]
**health_summary** | [**NamespacesOverviewHealthSummary**](NamespacesOverviewHealthSummary.md) |  | [optional]
**last_updated** | **datetime** |  |

## Example

```python
from aivo_sdk.models.namespaces_overview import NamespacesOverview

# TODO update the JSON string below
json = "{}"
# create an instance of NamespacesOverview from a JSON string
namespaces_overview_instance = NamespacesOverview.from_json(json)
# print the JSON string representation of the object
print(NamespacesOverview.to_json())

# convert the object into a dict
namespaces_overview_dict = namespaces_overview_instance.to_dict()
# create an instance of NamespacesOverview from a dict
namespaces_overview_from_dict = NamespacesOverview.from_dict(namespaces_overview_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
