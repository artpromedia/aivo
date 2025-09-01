# LearnerProfile


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**learner_id** | **str** |  | 
**bio** | **str** |  | [optional] 
**preferences** | [**LearnerProfilePreferences**](LearnerProfilePreferences.md) |  | 
**skills** | [**List[LearnerProfileSkillsInner]**](LearnerProfileSkillsInner.md) |  | 
**goals** | [**List[LearnerProfileGoalsInner]**](LearnerProfileGoalsInner.md) |  | 
**interests** | **List[str]** |  | [optional] 

## Example

```python
from aivo_sdk.models.learner_profile import LearnerProfile

# TODO update the JSON string below
json = "{}"
# create an instance of LearnerProfile from a JSON string
learner_profile_instance = LearnerProfile.from_json(json)
# print the JSON string representation of the object
print(LearnerProfile.to_json())

# convert the object into a dict
learner_profile_dict = learner_profile_instance.to_dict()
# create an instance of LearnerProfile from a dict
learner_profile_from_dict = LearnerProfile.from_dict(learner_profile_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


