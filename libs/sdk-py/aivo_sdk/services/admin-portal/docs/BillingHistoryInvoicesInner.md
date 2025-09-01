# BillingHistoryInvoicesInner


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**invoice_number** | **str** |  | 
**amount** | **float** | Invoice amount | 
**currency** | **str** |  | [optional] 
**status** | **str** |  | 
**due_date** | **date** |  | 
**paid_at** | **datetime** |  | 
**download_url** | **str** |  | [optional] 
**description** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.billing_history_invoices_inner import BillingHistoryInvoicesInner

# TODO update the JSON string below
json = "{}"
# create an instance of BillingHistoryInvoicesInner from a JSON string
billing_history_invoices_inner_instance = BillingHistoryInvoicesInner.from_json(json)
# print the JSON string representation of the object
print(BillingHistoryInvoicesInner.to_json())

# convert the object into a dict
billing_history_invoices_inner_dict = billing_history_invoices_inner_instance.to_dict()
# create an instance of BillingHistoryInvoicesInner from a dict
billing_history_invoices_inner_from_dict = BillingHistoryInvoicesInner.from_dict(billing_history_invoices_inner_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


