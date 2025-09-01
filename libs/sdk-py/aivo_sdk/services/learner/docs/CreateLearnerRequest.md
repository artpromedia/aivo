# CreateLearnerRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  | 
**email** | **str** |  | 
**first_name** | **str** |  | 
**last_name** | **str** |  | 
**timezone** | **str** |  | [optional] 
**language** | **str** |  | [optional] 
**department** | **str** |  | [optional] 
**job_title** | **str** |  | [optional] 
**manager** | **str** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 

## Example

```python
from aivo_sdk.models.create_learner_request import CreateLearnerRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateLearnerRequest from a JSON string
create_learner_request_instance = CreateLearnerRequest.from_json(json)
# print the JSON string representation of the object
print(CreateLearnerRequest.to_json())

# convert the object into a dict
create_learner_request_dict = create_learner_request_instance.to_dict()
# create an instance of CreateLearnerRequest from a dict
create_learner_request_from_dict = CreateLearnerRequest.from_dict(create_learner_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


