# NamespacesOverviewStatusCounts

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**active** | **int** | Namespaces that are active and ready |
**inactive** | **int** | Namespaces that are inactive/paused |
**initializing** | **int** | Namespaces currently being set up |
**error** | **int** | Namespaces with errors |

## Example

```python
from aivo_sdk.models.namespaces_overview_status_counts import NamespacesOverviewStatusCounts

# TODO update the JSON string below
json = "{}"
# create an instance of NamespacesOverviewStatusCounts from a JSON string
namespaces_overview_status_counts_instance = NamespacesOverviewStatusCounts.from_json(json)
# print the JSON string representation of the object
print(NamespacesOverviewStatusCounts.to_json())

# convert the object into a dict
namespaces_overview_status_counts_dict = namespaces_overview_status_counts_instance.to_dict()
# create an instance of NamespacesOverviewStatusCounts from a dict
namespaces_overview_status_counts_from_dict = NamespacesOverviewStatusCounts.from_dict(namespaces_overview_status_counts_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
