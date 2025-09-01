# NamespacesOverviewTopNamespacesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**namespace_id** | **str** |  | 
**learner_id** | **str** |  | 
**learner_name** | **str** |  | [optional] 
**status** | **str** |  | 
**storage_used** | **int** | Storage used by this namespace (MB) | 
**documents_count** | **int** | Number of documents in namespace | [optional] 
**last_activity** | **datetime** |  | 
**vector_count** | **int** | Number of vectors in namespace | [optional] 

## Example

```python
from aivo_sdk.models.namespaces_overview_top_namespaces_inner import NamespacesOverviewTopNamespacesInner

# TODO update the JSON string below
json = "{}"
# create an instance of NamespacesOverviewTopNamespacesInner from a JSON string
namespaces_overview_top_namespaces_inner_instance = NamespacesOverviewTopNamespacesInner.from_json(json)
# print the JSON string representation of the object
print(NamespacesOverviewTopNamespacesInner.to_json())

# convert the object into a dict
namespaces_overview_top_namespaces_inner_dict = namespaces_overview_top_namespaces_inner_instance.to_dict()
# create an instance of NamespacesOverviewTopNamespacesInner from a dict
namespaces_overview_top_namespaces_inner_from_dict = NamespacesOverviewTopNamespacesInner.from_dict(namespaces_overview_top_namespaces_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


