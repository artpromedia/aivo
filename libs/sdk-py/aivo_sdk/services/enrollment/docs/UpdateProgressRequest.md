# UpdateProgressRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**progress_percentage** | **float** |  | 
**time_spent_minutes** | **int** |  | 
**completed_modules** | **List[str]** |  | [optional] 
**current_module** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.update_progress_request import UpdateProgressRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateProgressRequest from a JSON string
update_progress_request_instance = UpdateProgressRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateProgressRequest.to_json())

# convert the object into a dict
update_progress_request_dict = update_progress_request_instance.to_dict()
# create an instance of UpdateProgressRequest from a dict
update_progress_request_from_dict = UpdateProgressRequest.from_dict(update_progress_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


