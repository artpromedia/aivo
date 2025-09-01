# TeamOverviewRecentActivity


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**new_users_this_week** | **int** |  | [optional] 
**new_users_this_month** | **int** |  | [optional] 
**last_user_joined** | **datetime** |  | [optional] 

## Example

```python
from aivo_sdk.models.team_overview_recent_activity import TeamOverviewRecentActivity

# TODO update the JSON string below
json = "{}"
# create an instance of TeamOverviewRecentActivity from a JSON string
team_overview_recent_activity_instance = TeamOverviewRecentActivity.from_json(json)
# print the JSON string representation of the object
print(TeamOverviewRecentActivity.to_json())

# convert the object into a dict
team_overview_recent_activity_dict = team_overview_recent_activity_instance.to_dict()
# create an instance of TeamOverviewRecentActivity from a dict
team_overview_recent_activity_from_dict = TeamOverviewRecentActivity.from_dict(team_overview_recent_activity_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


