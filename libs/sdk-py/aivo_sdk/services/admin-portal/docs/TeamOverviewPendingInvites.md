# TeamOverviewPendingInvites

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total** | **int** | Total pending invitations |
**by_role** | [**TeamOverviewPendingInvitesByRole**](TeamOverviewPendingInvitesByRole.md) |  |
**oldest_invite** | **datetime** | Date of oldest pending invite | [optional]

## Example

```python
from aivo_sdk.models.team_overview_pending_invites import TeamOverviewPendingInvites

# TODO update the JSON string below
json = "{}"
# create an instance of TeamOverviewPendingInvites from a JSON string
team_overview_pending_invites_instance = TeamOverviewPendingInvites.from_json(json)
# print the JSON string representation of the object
print(TeamOverviewPendingInvites.to_json())

# convert the object into a dict
team_overview_pending_invites_dict = team_overview_pending_invites_instance.to_dict()
# create an instance of TeamOverviewPendingInvites from a dict
team_overview_pending_invites_from_dict = TeamOverviewPendingInvites.from_dict(team_overview_pending_invites_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
