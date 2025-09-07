# TeamOverviewUsersByRole

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_admin** | **int** | Number of tenant administrators |
**instructor** | **int** | Number of instructors |
**learner** | **int** | Number of learners |
**total** | **int** | Total number of users | [optional]

## Example

```python
from aivo_sdk.models.team_overview_users_by_role import TeamOverviewUsersByRole

# TODO update the JSON string below
json = "{}"
# create an instance of TeamOverviewUsersByRole from a JSON string
team_overview_users_by_role_instance = TeamOverviewUsersByRole.from_json(json)
# print the JSON string representation of the object
print(TeamOverviewUsersByRole.to_json())

# convert the object into a dict
team_overview_users_by_role_dict = team_overview_users_by_role_instance.to_dict()
# create an instance of TeamOverviewUsersByRole from a dict
team_overview_users_by_role_from_dict = TeamOverviewUsersByRole.from_dict(team_overview_users_by_role_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
