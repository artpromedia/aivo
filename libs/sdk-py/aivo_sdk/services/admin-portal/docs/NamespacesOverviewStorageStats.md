# NamespacesOverviewStorageStats

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_storage_used** | **int** | Total storage used across all namespaces (MB) | [optional]
**average_storage_per_namespace** | **float** | Average storage per namespace (MB) | [optional]
**max_storage_used** | **int** | Maximum storage used by a single namespace (MB) | [optional]

## Example

```python
from aivo_sdk.models.namespaces_overview_storage_stats import NamespacesOverviewStorageStats

# TODO update the JSON string below
json = "{}"
# create an instance of NamespacesOverviewStorageStats from a JSON string
namespaces_overview_storage_stats_instance = NamespacesOverviewStorageStats.from_json(json)
# print the JSON string representation of the object
print(NamespacesOverviewStorageStats.to_json())

# convert the object into a dict
namespaces_overview_storage_stats_dict = namespaces_overview_storage_stats_instance.to_dict()
# create an instance of NamespacesOverviewStorageStats from a dict
namespaces_overview_storage_stats_from_dict = NamespacesOverviewStorageStats.from_dict(namespaces_overview_storage_stats_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
