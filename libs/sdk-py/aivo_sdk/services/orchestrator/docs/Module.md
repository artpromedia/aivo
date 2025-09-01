# Module


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**course_id** | **str** |  | 
**title** | **str** |  | 
**description** | **str** |  | [optional] 
**type** | **str** |  | 
**order** | **int** |  | 
**estimated_duration** | **int** | Estimated duration in minutes | 
**content_url** | **str** |  | [optional] 
**transcript_url** | **str** |  | [optional] 
**resources** | [**List[ModuleResourcesInner]**](ModuleResourcesInner.md) |  | [optional] 
**is_optional** | **bool** |  | [optional] [default to False]
**prerequisites** | **List[str]** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 
**created_at** | **datetime** |  | 
**updated_at** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.module import Module

# TODO update the JSON string below
json = "{}"
# create an instance of Module from a JSON string
module_instance = Module.from_json(json)
# print the JSON string representation of the object
print(Module.to_json())

# convert the object into a dict
module_dict = module_instance.to_dict()
# create an instance of Module from a dict
module_from_dict = Module.from_dict(module_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


