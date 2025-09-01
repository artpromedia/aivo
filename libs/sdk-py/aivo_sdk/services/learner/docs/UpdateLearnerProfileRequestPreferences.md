# UpdateLearnerProfileRequestPreferences


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**learning_style** | **str** |  | [optional] 
**difficulty_level** | **str** |  | [optional] 
**notifications_enabled** | **bool** |  | [optional] 
**email_digest** | **bool** |  | [optional] 
**preferred_learning_time** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.update_learner_profile_request_preferences import UpdateLearnerProfileRequestPreferences

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateLearnerProfileRequestPreferences from a JSON string
update_learner_profile_request_preferences_instance = UpdateLearnerProfileRequestPreferences.from_json(json)
# print the JSON string representation of the object
print(UpdateLearnerProfileRequestPreferences.to_json())

# convert the object into a dict
update_learner_profile_request_preferences_dict = update_learner_profile_request_preferences_instance.to_dict()
# create an instance of UpdateLearnerProfileRequestPreferences from a dict
update_learner_profile_request_preferences_from_dict = UpdateLearnerProfileRequestPreferences.from_dict(update_learner_profile_request_preferences_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


