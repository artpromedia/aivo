# TeamOverviewTopUsersInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**user_id** | **str** |  | [optional] 
**name** | **str** |  | [optional] 
**email** | **str** |  | [optional] 
**role** | **str** |  | [optional] 
**last_active** | **datetime** |  | [optional] 
**enrollments** | **int** |  | [optional] 

## Example

```python
from aivo_sdk.models.team_overview_top_users_inner import TeamOverviewTopUsersInner

# TODO update the JSON string below
json = "{}"
# create an instance of TeamOverviewTopUsersInner from a JSON string
team_overview_top_users_inner_instance = TeamOverviewTopUsersInner.from_json(json)
# print the JSON string representation of the object
print(TeamOverviewTopUsersInner.to_json())

# convert the object into a dict
team_overview_top_users_inner_dict = team_overview_top_users_inner_instance.to_dict()
# create an instance of TeamOverviewTopUsersInner from a dict
team_overview_top_users_inner_from_dict = TeamOverviewTopUsersInner.from_dict(team_overview_top_users_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


