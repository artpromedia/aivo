# ModuleResourcesInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | **str** |  | [optional]
**url** | **str** |  | [optional]
**type** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.module_resources_inner import ModuleResourcesInner

# TODO update the JSON string below
json = "{}"
# create an instance of ModuleResourcesInner from a JSON string
module_resources_inner_instance = ModuleResourcesInner.from_json(json)
# print the JSON string representation of the object
print(ModuleResourcesInner.to_json())

# convert the object into a dict
module_resources_inner_dict = module_resources_inner_instance.to_dict()
# create an instance of ModuleResourcesInner from a dict
module_resources_inner_from_dict = ModuleResourcesInner.from_dict(module_resources_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
