# Enrollment

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  |
**tenant_id** | **str** |  |
**learner_id** | **str** |  |
**course_id** | **str** |  |
**status** | **str** |  |
**enrolled_at** | **datetime** |  |
**started_at** | **datetime** |  | [optional]
**completed_at** | **datetime** |  | [optional]
**expires_at** | **datetime** |  | [optional]
**enrolled_by** | **str** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]
**created_at** | **datetime** |  |
**updated_at** | **datetime** |  |

## Example

```python
from aivo_sdk.models.enrollment import Enrollment

# TODO update the JSON string below
json = "{}"
# create an instance of Enrollment from a JSON string
enrollment_instance = Enrollment.from_json(json)
# print the JSON string representation of the object
print(Enrollment.to_json())

# convert the object into a dict
enrollment_dict = enrollment_instance.to_dict()
# create an instance of Enrollment from a dict
enrollment_from_dict = Enrollment.from_dict(enrollment_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
