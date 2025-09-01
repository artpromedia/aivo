# AwardAchievementRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**title** | **str** |  | 
**description** | **str** |  | 
**icon_url** | **str** |  | [optional] 
**badge_url** | **str** |  | [optional] 
**points** | **int** |  | [optional] [default to 0]
**metadata** | **Dict[str, object]** |  | [optional] 

## Example

```python
from aivo_sdk.models.award_achievement_request import AwardAchievementRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AwardAchievementRequest from a JSON string
award_achievement_request_instance = AwardAchievementRequest.from_json(json)
# print the JSON string representation of the object
print(AwardAchievementRequest.to_json())

# convert the object into a dict
award_achievement_request_dict = award_achievement_request_instance.to_dict()
# create an instance of AwardAchievementRequest from a dict
award_achievement_request_from_dict = AwardAchievementRequest.from_dict(award_achievement_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


