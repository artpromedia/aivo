# BillingHistorySummary

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_paid** | **float** | Total amount paid to date | [optional]
**total_outstanding** | **float** | Total outstanding amount | [optional]
**average_monthly_spend** | **float** | Average monthly spend | [optional]

## Example

```python
from aivo_sdk.models.billing_history_summary import BillingHistorySummary

# TODO update the JSON string below
json = "{}"
# create an instance of BillingHistorySummary from a JSON string
billing_history_summary_instance = BillingHistorySummary.from_json(json)
# print the JSON string representation of the object
print(BillingHistorySummary.to_json())

# convert the object into a dict
billing_history_summary_dict = billing_history_summary_instance.to_dict()
# create an instance of BillingHistorySummary from a dict
billing_history_summary_from_dict = BillingHistorySummary.from_dict(billing_history_summary_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
