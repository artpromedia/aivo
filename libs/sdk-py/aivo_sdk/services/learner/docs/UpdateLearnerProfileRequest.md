# UpdateLearnerProfileRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bio** | **str** |  | [optional] 
**preferences** | [**UpdateLearnerProfileRequestPreferences**](UpdateLearnerProfileRequestPreferences.md) |  | [optional] 
**interests** | **List[str]** |  | [optional] 

## Example

```python
from aivo_sdk.models.update_learner_profile_request import UpdateLearnerProfileRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateLearnerProfileRequest from a JSON string
update_learner_profile_request_instance = UpdateLearnerProfileRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateLearnerProfileRequest.to_json())

# convert the object into a dict
update_learner_profile_request_dict = update_learner_profile_request_instance.to_dict()
# create an instance of UpdateLearnerProfileRequest from a dict
update_learner_profile_request_from_dict = UpdateLearnerProfileRequest.from_dict(update_learner_profile_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


