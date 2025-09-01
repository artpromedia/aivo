# TeamOverview


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  | 
**users_by_role** | [**TeamOverviewUsersByRole**](TeamOverviewUsersByRole.md) |  | 
**pending_invites** | [**TeamOverviewPendingInvites**](TeamOverviewPendingInvites.md) |  | 
**recent_activity** | [**TeamOverviewRecentActivity**](TeamOverviewRecentActivity.md) |  | 
**top_users** | [**List[TeamOverviewTopUsersInner]**](TeamOverviewTopUsersInner.md) | Most active users in the tenant | [optional] 
**last_updated** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.team_overview import TeamOverview

# TODO update the JSON string below
json = "{}"
# create an instance of TeamOverview from a JSON string
team_overview_instance = TeamOverview.from_json(json)
# print the JSON string representation of the object
print(TeamOverview.to_json())

# convert the object into a dict
team_overview_dict = team_overview_instance.to_dict()
# create an instance of TeamOverview from a dict
team_overview_from_dict = TeamOverview.from_dict(team_overview_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


