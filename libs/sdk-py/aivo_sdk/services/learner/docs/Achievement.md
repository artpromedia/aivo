# Achievement


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**learner_id** | **str** |  | 
**type** | **str** |  | 
**title** | **str** |  | 
**description** | **str** |  | 
**icon_url** | **str** |  | [optional] 
**badge_url** | **str** |  | [optional] 
**points** | **int** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 
**earned_at** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.achievement import Achievement

# TODO update the JSON string below
json = "{}"
# create an instance of Achievement from a JSON string
achievement_instance = Achievement.from_json(json)
# print the JSON string representation of the object
print(Achievement.to_json())

# convert the object into a dict
achievement_dict = achievement_instance.to_dict()
# create an instance of Achievement from a dict
achievement_from_dict = Achievement.from_dict(achievement_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


