# NamespacesOverviewHealthSummary


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**health_score** | **float** | Overall health score of all namespaces | [optional] 
**common_issues** | [**List[NamespacesOverviewHealthSummaryCommonIssuesInner]**](NamespacesOverviewHealthSummaryCommonIssuesInner.md) |  | [optional] 

## Example

```python
from aivo_sdk.models.namespaces_overview_health_summary import NamespacesOverviewHealthSummary

# TODO update the JSON string below
json = "{}"
# create an instance of NamespacesOverviewHealthSummary from a JSON string
namespaces_overview_health_summary_instance = NamespacesOverviewHealthSummary.from_json(json)
# print the JSON string representation of the object
print(NamespacesOverviewHealthSummary.to_json())

# convert the object into a dict
namespaces_overview_health_summary_dict = namespaces_overview_health_summary_instance.to_dict()
# create an instance of NamespacesOverviewHealthSummary from a dict
namespaces_overview_health_summary_from_dict = NamespacesOverviewHealthSummary.from_dict(namespaces_overview_health_summary_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


