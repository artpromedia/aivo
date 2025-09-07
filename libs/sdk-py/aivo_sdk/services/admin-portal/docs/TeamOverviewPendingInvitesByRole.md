# TeamOverviewPendingInvitesByRole

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_admin** | **int** |  | [optional]
**instructor** | **int** |  | [optional]
**learner** | **int** |  | [optional]

## Example

```python
from aivo_sdk.models.team_overview_pending_invites_by_role import TeamOverviewPendingInvitesByRole

# TODO update the JSON string below
json = "{}"
# create an instance of TeamOverviewPendingInvitesByRole from a JSON string
team_overview_pending_invites_by_role_instance = TeamOverviewPendingInvitesByRole.from_json(json)
# print the JSON string representation of the object
print(TeamOverviewPendingInvitesByRole.to_json())

# convert the object into a dict
team_overview_pending_invites_by_role_dict = team_overview_pending_invites_by_role_instance.to_dict()
# create an instance of TeamOverviewPendingInvitesByRole from a dict
team_overview_pending_invites_by_role_from_dict = TeamOverviewPendingInvitesByRole.from_dict(team_overview_pending_invites_by_role_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
