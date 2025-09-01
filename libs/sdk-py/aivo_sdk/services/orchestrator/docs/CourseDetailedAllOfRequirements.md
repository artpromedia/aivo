# CourseDetailedAllOfRequirements


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**system_requirements** | **List[str]** |  | [optional] 
**software_requirements** | **List[str]** |  | [optional] 

## Example

```python
from aivo_sdk.models.course_detailed_all_of_requirements import CourseDetailedAllOfRequirements

# TODO update the JSON string below
json = "{}"
# create an instance of CourseDetailedAllOfRequirements from a JSON string
course_detailed_all_of_requirements_instance = CourseDetailedAllOfRequirements.from_json(json)
# print the JSON string representation of the object
print(CourseDetailedAllOfRequirements.to_json())

# convert the object into a dict
course_detailed_all_of_requirements_dict = course_detailed_all_of_requirements_instance.to_dict()
# create an instance of CourseDetailedAllOfRequirements from a dict
course_detailed_all_of_requirements_from_dict = CourseDetailedAllOfRequirements.from_dict(course_detailed_all_of_requirements_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


