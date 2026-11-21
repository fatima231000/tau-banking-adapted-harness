# Tool-contract registry (built from the KB)

Model `claude-opus-5-5`; tokens in/out 130196/61288; 0 entries dropped for unverifiable quotes.

| tool | source docs | prerequisite calls | preconditions | ordering | derived args |
|---|---|---|---|---|---|
| `activate_debit_card_8291` | 1 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823 | 9 | 4 | pin |
| `activate_debit_card_8292` | 1 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823 | 9 | 6 | expiration_date |
| `activate_debit_card_8293` | 1 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823 | 9 | 5 | - |
| `apply_checking_account_credit_5829` | 1 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173 | 8 | 2 | amount, amount, credit_type |
| `apply_credit_card_account_flag_6147` | 1 | get_closure_reason_history_8293, get_credit_card_accounts_by_user, get_current_time, get_pending_replacement_orders_5765, get_user_dispute_history_7291 | 8 | 2 | flag_type, expiration_date, reason |
| `apply_savings_account_credit_6831` | 2 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173 | 6 | 3 | amount, credit_type |
| `apply_statement_credit_8472` | 1 | get_credit_card_accounts_by_user | 2 | 2 | reason |
| `approve_credit_limit_increase_5847` | 1 | get_credit_card_accounts_by_user, get_credit_limit_increase_history_4829, get_pending_replacement_orders_5765, get_user_dispute_history_7291 | 8 | 3 | new_credit_limit |
| `change_debit_card_pin_6285` | 1 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823, get_user_information_by_id | 9 | 5 | - |
| `clear_debit_card_fraud_alert_4892` | 1 | get_user_information_by_id | 5 | 2 | reason, reason |
| `close_bank_account_7392` | 4 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173, get_current_time | 8 | 4 | - |
| `close_credit_card_account_7834` | 1 | get_credit_card_accounts_by_user, get_current_time, get_pending_replacement_orders_5765, get_user_dispute_history_7291 | 6 | 2 | user_id |
| `close_debit_card_4721` | 1 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173, get_current_time, get_debit_cards_by_account_id_7823, get_user_information_by_email | 7 | 5 | reason |
| `deny_credit_limit_increase_5848` | 1 | get_credit_card_accounts_by_user, get_credit_limit_increase_history_4829, get_pending_replacement_orders_5765, get_user_dispute_history_7291 | 8 | 4 | denial_reason |
| `file_credit_card_transaction_dispute_4829` | 1 | get_credit_card_accounts_by_user, get_credit_card_transactions_by_user, get_user_information_by_id | 4 | 1 | card_action, partial_refund_amount, eligible_for_provisional_credit, purchase_date |
| `file_debit_card_transaction_dispute_6281` | 1 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173, get_debit_cards_by_account_id_7823, get_debit_dispute_status_7483 | 8 | 2 | card_action, dispute_category, customer_max_liability_amount, written_statement_provided, transaction_id |
| `freeze_debit_card_3892` | 2 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823 | 5 | 5 | - |
| `log_credit_card_closure_reason_4521` | 1 | get_closure_reason_history_8293, get_credit_card_accounts_by_user, get_current_time, get_pending_replacement_orders_5765, get_user_dispute_history_7291 | 7 | 5 | closure_reason |
| `open_bank_account_4821` | 4 | get_all_user_accounts_by_user_id_3847, get_user_information_by_id | 18 | 5 | account_type, account_type, account_class, account_class, account_class, user_id |
| `order_debit_card_5739` | 2 | get_all_user_accounts_by_user_id_3847, get_current_time, get_debit_cards_by_account_id_7823, get_user_information_by_id | 14 | 8 | delivery_fee, design_fee, excess_replacement_fee, excess_replacement_fee |
| `order_replacement_credit_card_7291` | 2 | get_credit_card_accounts_by_user, get_user_information_by_id | 6 | 5 | reason, expedited_shipping |
| `pay_credit_card_from_checking_9182` | 1 | get_all_user_accounts_by_user_id_3847, get_credit_card_accounts_by_user, get_user_information_by_id | 5 | 5 | - |
| `request_temporary_debit_card_limit_increase_8374` | 1 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173, get_current_time, get_debit_cards_by_account_id_7823 | 6 | 1 | new_limit |
| `reset_debit_card_pin_6284` | 1 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823, get_user_information_by_id | 9 | 6 | - |
| `set_debit_card_recurring_block_7382` | 1 | get_user_information_by_id | 3 | 8 | block_recurring |
| `submit_credit_limit_increase_request_7392` | 1 | get_credit_card_accounts_by_user | 2 | 4 | - |
| `submit_interest_discrepancy_report_7294` | 2 | get_all_user_accounts_by_user_id_3847, get_bank_account_transactions_9173 | 3 | 3 | expected_apy, amount_difference |
| `transfer_funds_between_bank_accounts_7291` | 3 | get_all_user_accounts_by_user_id_3847 | 8 | 5 | source_account_id, destination_account_id, amount, source_account_id, destination_account_id |
| `unfreeze_debit_card_3893` | 1 | get_all_user_accounts_by_user_id_3847, get_debit_cards_by_account_id_7823 | 4 | 2 | - |
| `update_transaction_rewards_3847` | 1 | get_credit_card_accounts_by_user, get_credit_card_transactions_by_user | 5 | 5 | new_rewards_earned, transaction_id |

## Contracts

### `activate_debit_card_8291`
- **call first** `get_debit_cards_by_account_id_7823`: Look up the card to check issue_reason (must be new_account or first_card), PENDING status, and expiration date  
  > Look up the card in the debit_cards table and check the 'issue_reason' field to determine which activation tool to use (doc_bank_accounts_bank_accounts_(general)_024)
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm the linked checking account is still OPEN  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer identity must be verified (verify: get_user_information_by_id)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer must have the physical card in their possession (verify: None)  
  > Customer must have the physical card in their possession (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Debit card status must be PENDING (not already ACTIVE) (verify: get_debit_cards_by_account_id_7823)  
  > The debit card must be in PENDING status (not already ACTIVE) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Linked checking account must be OPEN (verify: get_all_user_accounts_by_user_id_3847)  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card must not be expired (verify: get_debit_cards_by_account_id_7823)  
  > Card must not be expired (check expiration_date) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card issue_reason must be 'new_account' or 'first_card' (verify: get_debit_cards_by_account_id_7823)  
  > activate_debit_card_8291: Use for NEW cards (first-time card for this checking account, issue_reason = 'new_account' or 'first_card') (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card details provided by customer (last 4, expiration, CVV) must match the card on the customer's account (verify: get_debit_cards_by_account_id_7823)  
  > Verify the card details match the customer's account (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card is locked if customer provides incorrect card details 2 times; must not proceed and must direct to branch (verify: None)  
  > If the customer provides incorrect card details 2 times, the card will be locked for security and they must visit a branch in person (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** PIN must be exactly 4 digits, not sequential or repeating (verify: None)  
  > Ask customer to set a 4-digit PIN for the card (must be exactly 4 digits, cannot be sequential like 1234 or repeating like 1111) (doc_bank_accounts_bank_accounts_(general)_024)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Check card issue_reason to select the correct activation tool
- **must_happen_before_this_call**: Verify card details match the customer's account
- **must_happen_after_this_call**: Confirm activation was successful
- **derived** `pin`: Must be exactly 4 digits chosen by customer; reject sequential (e.g., 1234) or repeating (e.g., 1111) values

### `activate_debit_card_8292`
- **call first** `get_debit_cards_by_account_id_7823`: Look up the card's issue_reason (must be lost/stolen/fraud), status (PENDING), and expiration date before activation.  
  > Look up the card in the debit_cards table and check the 'issue_reason' field to determine which activation tool to use (doc_bank_accounts_bank_accounts_(general)_024)
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm the linked checking account is still OPEN and identify the checking account for card lookup.  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card's issue_reason must be 'lost', 'stolen', or 'fraud' (replacement card). (verify: get_debit_cards_by_account_id_7823)  
  > activate_debit_card_8292: Use for REPLACEMENT cards (replacing lost/stolen/fraud cards, issue_reason = 'lost', 'stolen', or 'fraud') (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer identity must be verified. (verify: None)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer must have the physical card in their possession. (verify: None)  
  > Customer must have the physical card in their possession (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Debit card must be in PENDING status (not already ACTIVE). (verify: get_debit_cards_by_account_id_7823)  
  > The debit card must be in PENDING status (not already ACTIVE) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Linked checking account must still be OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card must not be expired. (verify: get_debit_cards_by_account_id_7823)  
  > Card must not be expired (check expiration_date) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card details provided by customer (last 4, expiration, CVV) must match the customer's account records. (verify: get_debit_cards_by_account_id_7823)  
  > Verify the card details match the customer's account (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer must not have provided incorrect card details 2 times (card would be locked; must visit branch). (verify: None)  
  > If the customer provides incorrect card details 2 times, the card will be locked for security and they must visit a branch in person (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** PIN must be exactly 4 digits, not sequential (e.g. 1234) or repeating (e.g. 1111). (verify: None)  
  > Ask customer to set a 4-digit PIN for the card (must be exactly 4 digits, cannot be sequential like 1234 or repeating like 1111) (doc_bank_accounts_bank_accounts_(general)_024)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Check the card's issue_reason to select the correct activation tool
- **must_happen_after_this_call**: Remind customer to review recent transactions for unauthorized charges
- **must_happen_after_this_call**: Ask if they have noticed suspicious activity on their account
- **must_happen_after_this_call**: Recommend changing online banking password if fraud was suspected
- **must_happen_after_this_call**: Confirm activation was successful
- **derived** `expiration_date`: Must be supplied in MM/YY format.

### `activate_debit_card_8293`
- **call first** `get_debit_cards_by_account_id_7823`: Look up the card's issue_reason, status (PENDING), and expiration date to confirm this reissue activation tool is correct and the card is eligible.  
  > Look up the card in the debit_cards table and check the 'issue_reason' field to determine which activation tool to use (doc_bank_accounts_bank_accounts_(general)_024)
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm the linked checking account is still OPEN.  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card issue_reason must be 'expired', 'damaged', 'upgrade', or 'bank_reissue'. (verify: get_debit_cards_by_account_id_7823)  
  > activate_debit_card_8293: Use for REISSUED cards (expiration renewal, damaged card, design upgrade, or bank-initiated, issue_reason = 'expired', 'damaged', 'upgrade', or 'bank_reissue') (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer must be verified. (verify: None)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Customer must have the physical card in their possession. (verify: None)  
  > Customer must have the physical card in their possession (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Debit card must be in PENDING status, not already ACTIVE. (verify: get_debit_cards_by_account_id_7823)  
  > The debit card must be in PENDING status (not already ACTIVE) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Linked checking account must be OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card must not be expired. (verify: get_debit_cards_by_account_id_7823)  
  > Card must not be expired (check expiration_date) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card details provided by customer must match the customer's account. (verify: get_debit_cards_by_account_id_7823)  
  > Verify the card details match the customer's account (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** PIN must be exactly 4 digits and not sequential or repeating. (verify: None)  
  > Ask customer to set a 4-digit PIN for the card (must be exactly 4 digits, cannot be sequential like 1234 or repeating like 1111) (doc_bank_accounts_bank_accounts_(general)_024)
- **condition** Card not locked from 2 incorrect card detail attempts; if locked, customer must visit a branch. (verify: None)  
  > If the customer provides incorrect card details 2 times, the card will be locked for security and they must visit a branch in person (doc_bank_accounts_bank_accounts_(general)_024)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Check card issue_reason to select the correct activation tool
- **must_happen_after_this_call**: Confirm activation was successful
- **must_happen_after_this_call**: Inform customer old card remains active for 24-hour grace period
- **must_happen_after_this_call**: Remind customer to update recurring payments if card number changed

### `apply_checking_account_credit_5829`
- **call first** `get_bank_account_transactions_9173`: Check transaction history to confirm the rebate has not already been applied or to confirm each fee discrepancy  
  > Confirm the rebate has not already been applied by checking the account's transaction history (doc_bank_accounts_bank_accounts_(general)_017)
- **call first** `get_all_user_accounts_by_user_id_3847`: Verify account ownership and confirm the account is a checking account  
  > Confirm the account is a checking account (credits cannot be applied to savings or other account types) (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** Customer identity and account ownership must be verified (verify: get_all_user_accounts_by_user_id_3847)  
  > Verify the customer's identity and account ownership (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** The account must be a checking account, not savings or other type (verify: get_all_user_accounts_by_user_id_3847)  
  > Credits may ONLY be applied to checking accounts. Savings accounts and other account types are not eligible. (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** Credit only for a missing rebate or a fee mischarge (otherwise supervisor approval required) (verify: None)  
  > Credits may only be applied for the two circumstances listed above. Do not apply credits for any other reason without supervisor approval. (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** For rebate credits, customer must meet rebate eligibility requirements (verify: None)  
  > Verify the customer is eligible for the rebate based on documented rebate policies (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** For rebate credits, the rebate must not already have been applied per transaction history (verify: get_bank_account_transactions_9173)  
  > Confirm the rebate has not already been applied by checking the account's transaction history (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** For fee refunds, each fee discrepancy must be confirmed in transaction history (verify: get_bank_account_transactions_9173)  
  > Check the transaction history to confirm each fee discrepancy (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** Tool may be called only once per checking account per interaction; 14-day cooldown after a credit on the same account (verify: get_bank_account_transactions_9173)  
  > After a credit is applied to a checking account, the system enforces a 14-day cooldown period before another credit can be applied to that same account. (doc_bank_accounts_bank_accounts_(general)_017)
- **condition** Amount must be greater than 0 (verify: None)  
  > amount: The positive dollar amount to credit (must be greater than 0) (doc_bank_accounts_bank_accounts_(general)_017)
- **must_happen_after_this_call**: Inform the customer of the applied credit and new account balance
- **must_happen_before_this_call**: Calculate the correct credit amount based on rebate policy or overcharged fee
- **derived** `amount`: Net correction across all identified fee discrepancies (and/or rebate amount per policy), combined into a single total if multiple corrections; exact, no rounding
- **derived** `amount`: If multiple corrections needed on same account, combine into one total amount
- **derived** `credit_type`: 'rebate_credit' for missing rebates, 'fee_refund' for incorrect fees; when combined, use the type applying to the majority of corrections

### `apply_credit_card_account_flag_6147`
- **call first** `get_user_dispute_history_7291`: Confirm the account has no active or pending transaction disputes (closure eligibility check before retention offers).  
  > Pending disputes: The account must not have any active or pending transaction disputes. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_pending_replacement_orders_5765`: Confirm there is no pending replacement card order on the account.  
  > No pending replacement cards: If a replacement has been ordered and not yet received or activated, a closure cannot proceed. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_credit_card_accounts_by_user`: Verify account age (at least 60 days), no outstanding balance, and customer tenure of 2+ years.  
  > Minimum account age: The account must be open for at least 60 days. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_closure_reason_history_8293`: Check for closure reason records within the past year; if any exist, retention offers are skipped.  
  > Use the get_closure_reason_history_8293 tool to determine whether this specific credit card account has any closure reason records within the past year. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_current_time`: Determine today's date to compute the expiration date one year from today.  
  > - expiration_date (string, required): Set to a date a year from today in MM/DD/YYYY format. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no active or pending transaction disputes. (verify: get_user_dispute_history_7291)  
  > Pending disputes: The account must not have any active or pending transaction disputes. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no pending replacement card orders. (verify: get_pending_replacement_orders_5765)  
  > No pending replacement cards: If a replacement has been ordered and not yet received or activated, a closure cannot proceed. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has been open for at least 60 days. (verify: get_credit_card_accounts_by_user)  
  > Minimum account age: The account must be open for at least 60 days. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no outstanding balance. (verify: get_credit_card_accounts_by_user)  
  > Outstanding balance: The account must have no outstanding balance. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** All closure eligibility requirements are met; otherwise no retention offers may be made. (verify: None)  
  > If any requirement is not met, explain what must be resolved and do not proceed with retention offers. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no closure reason records within the past year (otherwise skip retention offers). (verify: get_closure_reason_history_8293)  
  > If records exist for this account within that time frame, skip retention offers and proceed directly to processing the closure. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The customer's stated reason for closing is annual fee concerns. (verify: None)  
  > Annual fee concerns: If they have been a customer for 2+ years, offer to waive their annual fee for one year as a loyalty benefit. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The customer has been a customer for 2 or more years; otherwise offer a downgrade instead of a fee waiver. (verify: get_credit_card_accounts_by_user)  
  > If they have been a customer for less than 2 years, offer a permanent downgrade to a no-annual-fee card while preserving account history. (doc_credit_cards_credit_card_account_logistics_003)
- **must_happen_before_this_call**: Check closure reason history with get_closure_reason_history_8293 (Step 2).
- **must_happen_before_this_call**: Ask the customer why they want to close and log it with log_credit_card_closure_reason_4521 (Step 3).
- **derived** `flag_type`: Use 'annual_fee_waived' for the annual fee waiver.
- **derived** `expiration_date`: One year from today's date, in MM/DD/YYYY format.
- **derived** `reason`: Use 'loyalty_benefit' for long-tenured (2+ years) customers.

### `apply_savings_account_credit_6831`
- **call first** `get_all_user_accounts_by_user_id_3847`: Verify account ownership, confirm the account is a savings account, and check APY components for interest corrections  
  > Before applying: Verify the customer's account details and APY components using get_all_user_accounts_by_user_id_3847, review transaction history using get_bank_account_transactions_9173 to confirm the interest amount credited, calculate the correct interest amount based on documented APY rates and bonuses, determine the difference between expected and actual interest. (doc_bank_accounts_bank_accounts_(general)_043)
- **call first** `get_bank_account_transactions_9173`: Review transaction history to confirm the interest amount credited (or the incorrect fee charged)  
  > Before applying: Verify the customer's account details and APY components using get_all_user_accounts_by_user_id_3847, review transaction history using get_bank_account_transactions_9173 to confirm the interest amount credited, calculate the correct interest amount based on documented APY rates and bonuses, determine the difference between expected and actual interest. (doc_bank_accounts_bank_accounts_(general)_043)
- **condition** Customer's identity and account ownership have been verified (verify: get_all_user_accounts_by_user_id_3847)  
  > 1) Verify the customer's identity and account ownership (doc_bank_accounts_bank_accounts_(general)_043)
- **condition** The target account is a savings account (verify: get_all_user_accounts_by_user_id_3847)  
  > 2) Confirm the account is a savings account (doc_bank_accounts_bank_accounts_(general)_043)
- **condition** The customer meets one of the eligible circumstances (interest correction due to system error, incorrectly charged fee, or goodwill for significant inconvenience due to bank error) (verify: get_bank_account_transactions_9173)  
  > 3) Verify the customer meets one of the eligible circumstances listed above (doc_bank_accounts_bank_accounts_(general)_043)
- **condition** For fee refunds, the fee must have been incorrectly charged to the savings account (e.g., customer within withdrawal limits or met balance requirement) (verify: get_bank_account_transactions_9173)  
  > Fee Refunds: If a fee was incorrectly charged to the savings account (e.g., excess withdrawal fee charged when customer was within limits, monthly maintenance fee charged when balance requirement was met), the agent may apply a credit to refund the incorrect fee. (doc_bank_accounts_bank_accounts_(general)_043)
- **condition** Goodwill credits over $25 typically require supervisor approval (verify: None)  
  > Goodwill credits should be rare and typically require supervisor approval for amounts over $25. (doc_bank_accounts_bank_accounts_(general)_043)
- **condition** Amount must be a positive number greater than 0 (verify: None)  
  > - amount (number): The positive dollar amount to credit (must be greater than 0) (doc_bank_accounts_bank_accounts_(general)_043)
- **must_happen_after_this_call**: Submit interest discrepancy report using submit_interest_discrepancy_report_7294 (for interest corrections)
- **must_happen_after_this_call**: Inform the customer of the applied credit and new account balance
- **must_happen_before_this_call**: Calculate the correct credit amount based on the discrepancy or fee
- **derived** `amount`: For interest corrections, the difference between the expected interest (from documented APY rates and bonuses) and actual interest credited; for fee refunds, the incorrectly charged fee amount
- **derived** `credit_type`: 'interest_correction' for APY/interest calculation errors, 'fee_refund' for incorrect fee charges, 'goodwill_credit' for customer service gestures due to bank error

### `apply_statement_credit_8472`
- **call first** `get_credit_card_accounts_by_user`: Look up the credit_card_account_id to which the credit will be applied.  
  > credit_card_account_id (string, required) - The credit card account ID to apply the credit to. This can be found by calling get_credit_card_accounts_by_user. (doc_credit_cards_credit_cards_(general)_017)
- **condition** The amount must be a positive number in dollars. (verify: None)  
  > amount (number, required) - The credit amount in dollars. Must be a positive number (e.g., 25.00 for a $25 credit). (doc_credit_cards_credit_cards_(general)_017)
- **condition** The reason must be exactly one of the allowed enumerated values. (verify: None)  
  > reason (string, required) - The reason for the statement credit. Must be exactly one of: (doc_credit_cards_credit_cards_(general)_017)
- **must_happen_before_this_call**: Unlock the tool by calling unlock_discoverable_agent_tool with apply_statement_credit_8472.
- **must_happen_after_this_call**: Verify the credit appears as a negative transaction in the customer's credit card transaction history (get_credit_card_transactions_by_user) and reduces the statement balance.
- **derived** `reason`: Map the purpose of the credit to the matching enum value (e.g., late fee reversal -> 'late_fee_reversal', courtesy credit -> 'goodwill_adjustment', billing error -> 'error_correction'; 'other' only if none apply).

### `approve_credit_limit_increase_5847`
- **call first** `get_credit_limit_increase_history_4829`: Check whether a CLI request was submitted within the card tier's cooldown period.  
  > Cooldown Period: Use the get_credit_limit_increase_history_4829 tool to check if the customer has submitted a request within the cooldown period for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **call first** `get_credit_card_accounts_by_user`: Check account age, card tier, current limit, balance/past-due status, and credit utilization.  
  > Account Age: Verify the account has been open for the minimum required days for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **call first** `get_user_dispute_history_7291`: Verify the account has no active disputes.  
  > No Pending Disputes: Verify the account has no active disputes. (doc_credit_cards_credit_card_account_logistics_007)
- **call first** `get_pending_replacement_orders_5765`: Verify there are no outstanding replacement card orders for the account.  
  > No Pending Replacement Cards: Verify there are no outstanding replacement card orders for this account. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Requested increase amount is within the maximum allowed for the customer's card tier. (verify: get_credit_card_accounts_by_user)  
  > BEFORE submitting any CLI request, verify that the customer's requested increase amount is within the maximum allowed for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Account has been open for at least the minimum required days for its card tier. (verify: get_credit_card_accounts_by_user)  
  > Account Age: Verify the account has been open for the minimum required days for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** No CLI request was submitted within the cooldown period for the card tier (excluding the current submission). (verify: get_credit_limit_increase_history_4829)  
  > If a request exists within this period, deny the new request and inform the customer when they will be eligible to submit again. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Account has no active/pending disputes. (verify: get_user_dispute_history_7291)  
  > No Pending Disputes: Verify the account has no active disputes. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** No pending replacement card orders for the account. (verify: get_pending_replacement_orders_5765)  
  > If a replacement is pending, the CLI cannot be processed until the replacement is delivered or cancelled. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Account is in good standing: current with no past-due balance. (verify: get_credit_card_accounts_by_user)  
  > Account Good Standing: The account must be current with no past-due balance. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Current credit utilization is below the maximum threshold for the card tier. (verify: get_credit_card_accounts_by_user)  
  > Credit Utilization: Verify current utilization is below the maximum threshold for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** All eligibility criteria must be checked before an approval decision; all must be met. (verify: None)  
  > You MUST check ALL of the following eligibility criteria before making an approval or denial decision as this ensures complete audit records. (doc_credit_cards_credit_card_account_logistics_007)
- **must_happen_before_this_call**: Submit the CLI request using submit_credit_limit_increase_request_7392.
- **must_happen_before_this_call**: Verify all eligibility criteria after submitting the request.
- **must_happen_after_this_call**: Inform the customer of the decision and confirm the new credit limit.
- **derived** `new_credit_limit`: New total credit limit = current credit limit + the confirmed requested increase amount (not the increase amount itself).

### `change_debit_card_pin_6285`
- **call first** `get_user_information_by_id`: Verify customer identity and obtain date of birth to ensure the new PIN is not the birth year or birth month/day  
  > Cannot be the customer's birth year or birth month/day (doc_bank_accounts_bank_accounts_(general)_027)
- **call first** `get_all_user_accounts_by_user_id_3847`: Identify the customer's checking accounts to confirm the debit card belongs to the customer  
  > Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_027)
- **call first** `get_debit_cards_by_account_id_7823`: Confirm the card belongs to the customer's account and is in ACTIVE status  
  > Card must be in ACTIVE status (cannot change PIN on FROZEN, PENDING, or CLOSED cards) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Customer identity must be verified (verify: get_user_information_by_id)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Customer must own the debit card (card is linked to one of the customer's accounts) (verify: get_debit_cards_by_account_id_7823)  
  > Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Debit card status must be ACTIVE (not FROZEN, PENDING, or CLOSED) (verify: get_debit_cards_by_account_id_7823)  
  > Card must be in ACTIVE status (cannot change PIN on FROZEN, PENDING, or CLOSED cards) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** If the card is frozen, it must be unfrozen first (verify: get_debit_cards_by_account_id_7823)  
  > If customer's card is frozen, they must unfreeze it first before changing PIN (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Customer must confirm their current PIN (verify: None)  
  > Ask customer to confirm their current PIN for additional security (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** New PIN must be exactly 4 digits (verify: None)  
  > Must be exactly 4 digits (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** New PIN cannot be sequential (e.g., 1234, 4321) (verify: None)  
  > Cannot be sequential (e.g., 1234, 4321) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** New PIN cannot be all the same digit (verify: None)  
  > Cannot be all the same digit (e.g., 1111) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** New PIN cannot be the customer's birth year or birth month/day (verify: get_user_information_by_id)  
  > Cannot be the customer's birth year or birth month/day (doc_bank_accounts_bank_accounts_(general)_027)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Ask customer to confirm current PIN
- **must_happen_before_this_call**: Ask customer for new 4-digit PIN and validate it meets security requirements
- **must_happen_before_this_call**: Unfreeze the card if it is frozen
- **must_happen_after_this_call**: Confirm to the customer the PIN has been changed (without reading back the PIN)

### `clear_debit_card_fraud_alert_4892`
- **call first** `get_user_information_by_id`: Retrieve the customer's on-file details (DOB, email, phone, address) so the customer's identity can be verified before clearing the alert or block.  
  > Always verify the customer's identity before using this tool. (doc_bank_accounts_bank_accounts_(general)_039)
- **condition** The customer's identity has been verified. (verify: get_user_information_by_id)  
  > Always verify the customer's identity before using this tool. (doc_bank_accounts_bank_accounts_(general)_039)
- **condition** The fraud alert is not bank-initiated. Bank-initiated alerts cannot be cleared by this tool and must be transferred to the security team. (verify: get_debit_cards_by_account_id_7823)  
  > This tool CANNOT clear bank-initiated fraud alerts. (doc_bank_accounts_bank_accounts_(general)_039)
- **condition** For fraud alerts: the alert was customer-initiated and the customer confirms their recent transactions are legitimate. (verify: None)  
  > For fraud alerts: The alert was customer-initiated AND customer confirms their recent transactions are legitimate (doc_bank_accounts_bank_accounts_(general)_039)
- **condition** For velocity blocks: the customer provides a reasonable explanation for the unusual activity, and the explanation is not suspicious or inconsistent. (verify: None)  
  > For velocity blocks: Customer provides a reasonable explanation for the unusual activity (e.g., shopping spree, travel) (doc_bank_accounts_bank_accounts_(general)_039)
- **condition** The customer does not report transactions they did not make. If they do, escalate to the security team instead of clearing. (verify: None)  
  > Customer reports transactions they did not make (doc_bank_accounts_bank_accounts_(general)_039)
- **must_happen_before_this_call**: Verify the customer's identity.
- **must_happen_after_this_call**: Document in the interaction notes why the alert or block was cleared.
- **derived** `reason`: Use 'customer_verified' when clearing a customer-initiated fraud alert after identity verification and the customer's confirmation that the transactions are legitimate.
- **derived** `reason`: Use 'velocity_clear' when clearing a velocity block after identity verification.

### `close_bank_account_7392`
- **call first** `get_all_user_accounts_by_user_id_3847`: Check the account's status, current_holdings balance, account type/tier and opening date, plus the customer's other business checking and savings accounts.  
  > Account status is OPEN (doc_bank_accounts_bank_accounts_(general)_005)
- **call first** `get_bank_account_transactions_9173`: Verify there are no pending transactions on the account being closed.  
  > No pending transactions for this account (doc_bank_accounts_bank_accounts_(general)_005)
- **call first** `get_current_time`: Determine whether the account is within the early closure fee window for its tier.  
  > Early closure fee: $15 if closed within 30 days (doc_bank_accounts_bank_accounts_(general)_005)
- **condition** If an early closure fee applies, current_holdings must be at least the fee amount; otherwise current_holdings must be $0. (verify: get_all_user_accounts_by_user_id_3847)  
  > If an early closure fee applies, the account balance must be at least the fee amount; otherwise, account balance (current_holdings) must be $0. (doc_bank_accounts_bank_accounts_(general)_005)
- **condition** Account status is OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > Account status is OPEN (doc_bank_accounts_bank_accounts_(general)_006)
- **condition** No pending transactions exist for the account. (verify: get_bank_account_transactions_9173)  
  > No pending transactions for this account (doc_bank_accounts_bank_accounts_(general)_006)
- **condition** For a business checking account, the customer has no linked business savings accounts that are still OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > Customer has no linked business savings accounts that are still OPEN (close those first) (doc_bank_accounts_bank_accounts_(general)_007)
- **condition** For a business savings account, the customer must keep at least one active business checking account. (verify: get_all_user_accounts_by_user_id_3847)  
  > Customer must have at least one active business checking account remaining (business savings requires a linked business checking account) (doc_bank_accounts_bank_accounts_(general)_008)
- **condition** ELITE tier personal savings accounts require manager approval. (verify: None)  
  > For ELITE tier, obtain manager approval before proceeding. (doc_bank_accounts_bank_accounts_(general)_006)
- **condition** PREMIUM tier business checking accounts require supervisor review, and ELITE tier ones require manager approval. (verify: None)  
  > For PREMIUM tier, obtain supervisor review. For ELITE tier, obtain manager approval. (doc_bank_accounts_bank_accounts_(general)_007)
- **condition** PREMIUM tier business savings accounts require supervisor review, and ELITE tier ones require manager approval. (verify: None)  
  > For PREMIUM tier, obtain supervisor review. For ELITE tier, obtain manager approval. (doc_bank_accounts_bank_accounts_(general)_008)
- **must_happen_before_this_call**: Verify that all pre-closure requirements are met.
- **must_happen_before_this_call**: Determine the account tier and the applicable fees and notice period.
- **must_happen_before_this_call**: Close any linked OPEN business savings accounts before closing a business checking account.
- **must_happen_before_this_call**: Obtain manager approval for ELITE tier personal savings accounts.

### `close_credit_card_account_7834`
- **call first** `get_credit_card_accounts_by_user`: Look up the customer's credit card accounts to obtain the account ID and check the outstanding balance and account age  
  > This can be found in the customer's account profile or by looking up their credit card accounts. (doc_credit_cards_credit_card_account_logistics_002)
- **call first** `get_user_dispute_history_7291`: Check that the credit card account has no pending disputes  
  > No pending disputes (pending disputes allowed: No) (doc_credit_cards_credit_card_account_logistics_002)
- **call first** `get_pending_replacement_orders_5765`: Check that the account has no pending replacement card orders  
  > No pending replacement cards (doc_credit_cards_credit_card_account_logistics_002)
- **call first** `get_current_time`: Determine the current date to compute whether the account is at least 60 days old  
  > Account age at least 60 days (doc_credit_cards_credit_card_account_logistics_002)
- **condition** The customer's identity has been verified using standard verification procedures (verify: get_user_information_by_id)  
  > Verify the customer's identity using standard verification procedures. (doc_credit_cards_credit_card_account_logistics_002)
- **condition** The credit card account's outstanding balance is exactly $0.00 (verify: get_credit_card_accounts_by_user)  
  > Outstanding balance must be $0.00 dollars (doc_credit_cards_credit_card_account_logistics_002)
- **condition** There are no pending disputes on the credit card account (verify: get_user_dispute_history_7291)  
  > No pending disputes (pending disputes allowed: No) (doc_credit_cards_credit_card_account_logistics_002)
- **condition** The credit card account is at least 60 days old (opening date at least 60 days before the current date) (verify: get_credit_card_accounts_by_user)  
  > Account age at least 60 days (doc_credit_cards_credit_card_account_logistics_002)
- **condition** The credit card account has no pending replacement card orders (verify: get_pending_replacement_orders_5765)  
  > No pending replacement cards (doc_credit_cards_credit_card_account_logistics_002)
- **condition** The user_id must match the authenticated user requesting the closure (verify: None)  
  > This should match the authenticated user. (doc_credit_cards_credit_card_account_logistics_002)
- **must_happen_before_this_call**: Verify the customer's identity
- **must_happen_before_this_call**: Confirm all closure eligibility requirements are met ($0 balance, no pending disputes, account age >= 60 days, no pending replacement cards)
- **derived** `user_id`: Must be the user_id of the authenticated customer requesting the closure

### `close_debit_card_4721`
- **call first** `get_user_information_by_email`: Retrieve the customer's details to verify identity before closing the card.  
  > Verify customer identity using standard verification procedures (doc_bank_accounts_bank_accounts_(general)_025)
- **call first** `get_all_user_accounts_by_user_id_3847`: Find the customer's checking accounts so card ownership can be confirmed (user_id matches).  
  > Customer must be the owner of the debit card (verify user_id matches) (doc_bank_accounts_bank_accounts_(general)_025)
- **call first** `get_debit_cards_by_account_id_7823`: Check the card's status (ACTIVE or PENDING) and its date_issued for the minimum age check.  
  > The debit card must currently be in ACTIVE or PENDING status (doc_bank_accounts_bank_accounts_(general)_025)
- **call first** `get_bank_account_transactions_9173`: Check for pending or processing transactions and pending refunds on the card.  
  > No pending transactions: The card must not have any pending or processing transactions. (doc_bank_accounts_bank_accounts_(general)_025)
- **call first** `get_current_time`: Get today's date to work out the card's age from date_issued.  
  > Calculate this from the date_issued field. (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The customer has been identity-verified. (verify: get_user_information_by_email)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The customer owns the debit card: the card's account user_id matches the verified customer. (verify: get_all_user_accounts_by_user_id_3847)  
  > Customer must be the owner of the debit card (verify user_id matches) (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The debit card's status is ACTIVE or PENDING. (verify: get_debit_cards_by_account_id_7823)  
  > The debit card must currently be in ACTIVE or PENDING status (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The card has no pending or processing transactions. (verify: get_bank_account_transactions_9173)  
  > No pending transactions: The card must not have any pending or processing transactions. (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The card has no pending refunds, unless the customer acknowledges in writing that refunds will be credited to the linked checking account. (verify: get_bank_account_transactions_9173)  
  > If pending refunds exist, inform the customer they must wait for the refunds to process (typically 3-5 business days) or acknowledge in writing that the refunds will be credited to the linked checking account instead. (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The card has been active for at least 14 days since date_issued. This is waived when the reason is lost, stolen, or fraud_suspected. (verify: get_debit_cards_by_account_id_7823)  
  > Minimum card age: The debit card must have been active for at least 14 days. (doc_bank_accounts_bank_accounts_(general)_025)
- **condition** The lost, stolen, and fraud_suspected reasons bypass the minimum card age requirement. (verify: None)  
  > These reasons bypass the minimum card age requirement (requirement 6) for security purposes (doc_bank_accounts_bank_accounts_(general)_025)
- **must_happen_before_this_call**: Verify the customer's identity.
- **must_happen_before_this_call**: Ask the customer for the closure reason.
- **must_happen_before_this_call**: Check all eligibility requirements, and do not proceed if any is unmet.
- **must_happen_before_this_call**: For lost, stolen, or fraud_suspected reasons, ask the customer whether they want to order a replacement card immediately.
- **must_happen_after_this_call**: Confirm the closure and tell the customer the card is permanently deactivated, that recurring payments need updating, and how to order a new card.
- **derived** `reason`: Map the customer's stated reason to one of: lost, stolen, fraud_suspected, damaged, no_longer_needed, account_closing.

### `deny_credit_limit_increase_5848`
- **call first** `get_credit_limit_increase_history_4829`: Check whether a prior CLI request exists within the card tier's cooldown period.  
  > Cooldown Period: Use the get_credit_limit_increase_history_4829 tool to check if the customer has submitted a request within the cooldown period for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **call first** `get_credit_card_accounts_by_user`: Verify account age, past-due balance and credit utilization for the card account.  
  > You MUST check ALL of the following eligibility criteria before making an approval or denial decision as this ensures complete audit records. (doc_credit_cards_credit_card_account_logistics_007)
- **call first** `get_user_dispute_history_7291`: Verify the account has no active disputes.  
  > No Pending Disputes: Verify the account has no active disputes. (doc_credit_cards_credit_card_account_logistics_007)
- **call first** `get_pending_replacement_orders_5765`: Verify there are no outstanding replacement card orders for the account.  
  > No Pending Replacement Cards: Verify there are no outstanding replacement card orders for this account. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** All eligibility criteria (account age, cooldown, disputes, replacement cards, good standing, utilization) must have been checked before the denial decision. (verify: None)  
  > You MUST check ALL of the following eligibility criteria before making an approval or denial decision as this ensures complete audit records. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** At least one CLI requirement is not met. (verify: None)  
  > If any requirements are not met: (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Account age is checked against the minimum required days for the card tier. (verify: get_credit_card_accounts_by_user)  
  > Account Age: Verify the account has been open for the minimum required days for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** A prior CLI request within the tier cooldown period leads to denial. (verify: get_credit_limit_increase_history_4829)  
  > If a request exists within this period, deny the new request and inform the customer when they will be eligible to submit again. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Account has no active disputes is checked. (verify: get_user_dispute_history_7291)  
  > No Pending Disputes: Verify the account has no active disputes. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** No pending replacement card orders is checked. (verify: get_pending_replacement_orders_5765)  
  > If a replacement is pending, the CLI cannot be processed until the replacement is delivered or cancelled. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Account is current with no past-due balance is checked. (verify: get_credit_card_accounts_by_user)  
  > Account Good Standing: The account must be current with no past-due balance. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** Credit utilization is below the card tier maximum threshold is checked. (verify: get_credit_card_accounts_by_user)  
  > Credit Utilization: Verify current utilization is below the maximum threshold for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **must_happen_before_this_call**: Confirm the requested increase amount is within the card tier maximum.
- **must_happen_before_this_call**: Submit the CLI request with submit_credit_limit_increase_request_7392.
- **must_happen_before_this_call**: Verify all basic eligibility criteria after submitting the request.
- **must_happen_after_this_call**: Inform the customer of the denial reason and when they may reapply.
- **derived** `denial_reason`: Set to the enum value matching the failed eligibility criterion (e.g., cooldown violation -> 'cooldown_period_active', active dispute -> 'pending_disputes', pending replacement -> 'pending_replacement_card', past due -> 'past_due_balance', utilization too high -> 'high_utilization', account too new -> 'insufficient_account_age').

### `file_credit_card_transaction_dispute_4829`
- **call first** `get_user_information_by_id`: Retrieve the user's registered phone, email, and home address to populate the phone, email, and address arguments.  
  > 8. address (string) - The registered home address of the user. (doc_credit_cards_credit_cards_(general)_014)
- **call first** `get_credit_card_transactions_by_user`: Identify the disputed transaction, its ID, and the date it occurred (purchase_date).  
  > 10. purchase_date (string, format MM/DD/YYYY) - The date in which the disputed transaction occurred. (doc_credit_cards_credit_cards_(general)_014)
- **call first** `get_credit_card_accounts_by_user`: Determine the last 4 digits of the credit card on which the disputed transaction took place.  
  > 3. card_last_4_digits (string) - Last 4 digits of the credit card under which the disputed transaction took place. (doc_credit_cards_credit_cards_(general)_014)
- **condition** The tool must be unlocked before it is called. (verify: list_discoverable_agent_tools)  
  > First unlock the tool, then call it using call_discoverable_agent_tool with the tool name and a JSON string containing all the required arguments. (doc_credit_cards_credit_cards_(general)_014)
- **condition** The user must have been asked whether they tried to resolve the issue with the merchant first. (verify: None)  
  > 9. contacted_merchant (boolean) - Ask user: Did you try to resolve this with the merchant first? (doc_credit_cards_credit_cards_(general)_014)
- **condition** The user must have been asked when they noticed the issue. (verify: None)  
  > 11. issue_noticed_date (string, format MM/DD/YYYY) - Ask user when they noticed the issue. (doc_credit_cards_credit_cards_(general)_014)
- **condition** Provisional credit eligibility must be determined per the Provisional Credit Eligibility Guidelines. (verify: None)  
  > 15. eligible_for_provisional_credit (boolean) - Agent must determine this based on the Provisional Credit Eligibility Guidelines article in this knowledge base. (doc_credit_cards_credit_cards_(general)_014)
- **must_happen_before_this_call**: Unlock the file_credit_card_transaction_dispute_4829 tool.
- **derived** `card_action`: 'keep_active' if user wants to keep using current card; 'cancel_and_reissue' if the user wants the card replaced (whether replacement already ordered or cancellation part of this dispute).
- **derived** `partial_refund_amount`: Provide only when resolution_requested is 'partial_refund'.
- **derived** `eligible_for_provisional_credit`: Determined by applying the Provisional Credit Eligibility Guidelines.
- **derived** `purchase_date`: Date the disputed transaction occurred, formatted MM/DD/YYYY.

### `file_debit_card_transaction_dispute_6281`
- **call first** `get_bank_account_transactions_9173`: Look up the disputed transaction to get its transaction_id, date, and amount. Also checks the $1.00 minimum, the 60-day age limit, and ATM details.  
  > ID of the transaction being disputed. Use get_bank_account_transactions_9173 to find it. (doc_bank_accounts_bank_accounts_(general)_031)
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm the checking account linked to the debit card is OPEN and find its tier for the open-dispute limit.  
  > The debit card must be linked to an OPEN checking account (doc_bank_accounts_bank_accounts_(general)_031)
- **call first** `get_debit_cards_by_account_id_7823`: Identify the debit card ID linked to the checking account.  
  > The debit card must be linked to an OPEN checking account (doc_bank_accounts_bank_accounts_(general)_031)
- **call first** `get_debit_dispute_status_7483`: Count the open debit disputes on the account and compare against the tier maximum.  
  > Customer cannot exceed the maximum open disputes for their checking account tier: Entry Tier max 2, Mid Tier max 3, Premium Tier max 4, Elite Tier max 5. (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** Customer must be verified. (verify: get_user_information_by_id)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** Transaction amount must be at least $1.00. (verify: get_bank_account_transactions_9173)  
  > Transaction must be at least $1.00 (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** Transaction must be no more than 60 days old. (verify: get_bank_account_transactions_9173)  
  > Transaction must be within 60 days old (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** Open debit disputes on the checking account must be below the tier maximum (Entry 2, Mid 3, Premium 4, Elite 5). The limit applies per account. (verify: get_debit_dispute_status_7483)  
  > Dispute limits are per account, not per customer. (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** The debit card must be linked to an OPEN checking account. (verify: get_all_user_accounts_by_user_id_3847)  
  > The debit card must be linked to an OPEN checking account (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** For ATM disputes, determine whether the ATM was a Rho-Bank ATM or a third-party ATM. (verify: get_bank_account_transactions_9173)  
  > For ATM disputes, determine if it was a Rho-Bank ATM or third-party ATM (different processes apply) (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** Customer must be informed of their liability exposure based on reporting timing before proceeding. (verify: None)  
  > Before proceeding, inform the customer of their liability exposure based on when they noticed the unauthorized activity: (doc_bank_accounts_bank_accounts_(general)_031)
- **condition** For fraud disputes over $500, ask whether a police report was filed and recommend one if not. (verify: None)  
  > For fraud disputes over $500, ask if customer has filed a police report. (doc_bank_accounts_bank_accounts_(general)_031)
- **must_happen_before_this_call**: Inform the customer of their Regulation E liability exposure.
- **must_happen_after_this_call**: Perform the actual card action (e.g. freeze_debit_card_3892), using the most severe action across all disputes on the card.
- **derived** `card_action`: Map from dispute_category: card_present_fraud or card_not_present_fraud → close_and_reissue; unauthorized_transaction → freeze_pending_investigation; all other categories → keep_active.
- **derived** `dispute_category`: For an unauthorized transaction where fraud is suspected, use card_present_fraud (in-store/physical) or card_not_present_fraud (online/phone). Use unauthorized_transaction only when fraud is not suspected.
- **derived** `customer_max_liability_amount`: Reported within 2 business days of statement → 50; within 60 days → 500; after 60 days → -1 (unlimited).
- **derived** `written_statement_provided`: Set to true if the customer agrees to provide a written statement (this conversation can serve as the statement).
- **derived** `transaction_id`: When multiple duplicates exist, dispute the earliest (first) transaction.

### `freeze_debit_card_3892`
- **call first** `get_debit_cards_by_account_id_7823`: Confirm the debit card is in ACTIVE status and belongs to the customer's checking account before freezing.  
  > 3. Card must currently be in ACTIVE status (cannot freeze PENDING, CLOSED, or already FROZEN cards) (doc_bank_accounts_bank_accounts_(general)_026)
- **call first** `get_all_user_accounts_by_user_id_3847`: Identify the customer's checking accounts to confirm ownership of the debit card.  
  > 2. Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Customer identity must be verified. (verify: get_user_information_by_id)  
  > 1. Customer must be verified (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Customer must own the debit card (card linked to one of the customer's checking accounts). (verify: get_debit_cards_by_account_id_7823)  
  > 2. Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Card status must be ACTIVE (not PENDING, CLOSED, or FROZEN). (verify: get_debit_cards_by_account_id_7823)  
  > 3. Card must currently be in ACTIVE status (cannot freeze PENDING, CLOSED, or already FROZEN cards) (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Customer must be informed that new transactions, recurring payments will be declined, pending authorized transactions may still process, and they can unfreeze anytime. (verify: None)  
  > 3. Inform customer of the following: (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** If the customer confirms the card is lost/stolen, closing should be recommended instead of freezing. (verify: None)  
  > - If customer confirms the card is lost/stolen, recommend closing instead of freezing (doc_bank_accounts_bank_accounts_(general)_026)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Ask customer why they want to freeze the card
- **must_happen_before_this_call**: Inform customer of freeze consequences
- **must_happen_after_this_call**: Confirm the freeze was successful
- **must_happen_before_this_call**: When freezing as a dispute card action, file the debit card dispute(s) first (file_debit_card_transaction_dispute_6281)

### `log_credit_card_closure_reason_4521`
- **call first** `get_user_dispute_history_7291`: Confirm the credit card account has no active or pending transaction disputes before proceeding.  
  > Pending disputes: The account must not have any active or pending transaction disputes. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_pending_replacement_orders_5765`: Confirm there is no pending replacement card order for the account.  
  > No pending replacement cards: If a replacement has been ordered and not yet received or activated, a closure cannot proceed. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_credit_card_accounts_by_user`: Check account open date (at least 60 days) and that there is no outstanding balance.  
  > Minimum account age: The account must be open for at least 60 days. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_current_time`: Determine today's date to evaluate the 60-day account age and the past-year window for closure reason records.  
  > Use the get_closure_reason_history_8293 tool to determine whether this specific credit card account has any closure reason records within the past year. (doc_credit_cards_credit_card_account_logistics_003)
- **call first** `get_closure_reason_history_8293`: Check whether the account has closure reason records within the past year; if so, skip retention and go directly to closure (Step 6) without logging.  
  > Use the get_closure_reason_history_8293 tool to determine whether this specific credit card account has any closure reason records within the past year. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The credit card account has no active or pending transaction disputes. (verify: get_user_dispute_history_7291)  
  > Pending disputes: The account must not have any active or pending transaction disputes. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no pending replacement card order that has not been received or activated. (verify: get_pending_replacement_orders_5765)  
  > No pending replacement cards: If a replacement has been ordered and not yet received or activated, a closure cannot proceed. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has been open for at least 60 days. (verify: get_credit_card_accounts_by_user)  
  > Minimum account age: The account must be open for at least 60 days. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no outstanding balance. (verify: get_credit_card_accounts_by_user)  
  > Outstanding balance: The account must have no outstanding balance. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** If any eligibility requirement is not met, do not proceed with retention steps (including logging the reason). (verify: None)  
  > If any requirement is not met, explain what must be resolved and do not proceed with retention offers. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The account has no closure reason records within the past year; otherwise skip directly to processing the closure. (verify: get_closure_reason_history_8293)  
  > If records exist for this account within that time frame, skip retention offers and proceed directly to processing the closure. (doc_credit_cards_credit_card_account_logistics_003)
- **condition** The customer has been asked and has stated why they want to close the account. (verify: None)  
  > Ask the customer why they want to close their account. (doc_credit_cards_credit_card_account_logistics_003)
- **must_happen_before_this_call**: Verify closure eligibility (disputes, pending replacements, account age, balance).
- **must_happen_before_this_call**: Check closure reason history for the account within the past year.
- **must_happen_before_this_call**: Ask the customer why they want to close their account.
- **must_happen_after_this_call**: Address the customer's concern with tailored solutions based on the logged reason.
- **must_happen_after_this_call**: Make one retention offer based on card tier if the customer still wants to close.
- **derived** `closure_reason`: Map the customer's stated reason to one of the allowed values: 'annual_fee', 'not_using_card', 'found_better_card', 'unhappy_with_rewards', 'simplifying_finances', 'negative_experience', 'other'.

### `open_bank_account_4821`
- **call first** `get_user_information_by_id`: Confirm the customer's identity details and date of birth to check the 18+ age requirement for personal checking.  
  > 2. The customer is at least 18 years old. (doc_bank_accounts_bank_accounts_(general)_001)
- **call first** `get_all_user_accounts_by_user_id_3847`: Retrieve the customer's existing accounts to check account counts, statuses (OPEN/CLOSED/closed for cause/collections), balances, and tenure.  
  > 3. The customer does not exceed 4 personal checking accounts. (doc_bank_accounts_bank_accounts_(general)_001)
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm an active checking account exists with at least 14 days tenure and count existing personal savings accounts.  
  > - Count existing personal savings accounts; ensure the customer is below the 5 limit. (doc_bank_accounts_bank_accounts_(general)_002)
- **call first** `get_all_user_accounts_by_user_id_3847`: Check for an OPEN personal checking account with at least $500 balance, count business checking accounts, and check for CLOSED accounts.  
  > 5. The customer's existing checking account has a balance of at least $500. (doc_bank_accounts_bank_accounts_(general)_003)
- **call first** `get_all_user_accounts_by_user_id_3847`: Identify a qualifying OPEN business checking account (30+ days, $2,500+ balance), count business savings accounts, and check for negative balances.  
  > - OPEN business checking account identified and qualified (≥ 30 days open and ≥ $2,500 balance). (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** Customer identity is verified (all account types). (verify: get_user_information_by_id)  
  > 1. The customer is verified. (doc_bank_accounts_bank_accounts_(general)_001)
- **condition** Personal checking: customer is at least 18 years old. (verify: get_user_information_by_id)  
  > 2. The customer is at least 18 years old. (doc_bank_accounts_bank_accounts_(general)_001)
- **condition** Personal checking: customer does not exceed 4 personal checking accounts. (verify: get_all_user_accounts_by_user_id_3847)  
  > 3. The customer does not exceed 4 personal checking accounts. (doc_bank_accounts_bank_accounts_(general)_001)
- **condition** Personal checking: no checking accounts closed for cause in the past 6 months. (verify: get_all_user_accounts_by_user_id_3847)  
  > 4. The customer has no checking accounts closed for cause in the past 6 months. (doc_bank_accounts_bank_accounts_(general)_001)
- **condition** Personal savings: customer has at least one active Rho-Bank checking account. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Customer has at least one active Rho-Bank checking account. (doc_bank_accounts_bank_accounts_(general)_002)
- **condition** Personal savings: customer holds fewer than 5 personal savings accounts. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Customer currently holds fewer than 5 personal savings accounts. (doc_bank_accounts_bank_accounts_(general)_002)
- **condition** Personal savings: no accounts in collections and no negative balances. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Customer has no accounts in collections and no negative balances. (doc_bank_accounts_bank_accounts_(general)_002)
- **condition** Personal savings: checking account held for at least 14 days. (verify: get_all_user_accounts_by_user_id_3847)  
  > - The customer’s checking account tenure is at least 14 days. (doc_bank_accounts_bank_accounts_(general)_002)
- **condition** Business checking: at least one existing personal checking account with status OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > 2. The customer has at least one existing personal checking account with status OPEN. (doc_bank_accounts_bank_accounts_(general)_003)
- **condition** Business checking: customer does not exceed 6 business checking accounts. (verify: get_all_user_accounts_by_user_id_3847)  
  > 3. The customer does not exceed 6 business checking accounts. (doc_bank_accounts_bank_accounts_(general)_003)
- **condition** Business checking: customer has no accounts with status CLOSED. (verify: get_all_user_accounts_by_user_id_3847)  
  > 4. The customer has no accounts with status CLOSED. (doc_bank_accounts_bank_accounts_(general)_003)
- **condition** Business checking: existing checking account balance is at least $500. (verify: get_all_user_accounts_by_user_id_3847)  
  > 5. The customer's existing checking account has a balance of at least $500. (doc_bank_accounts_bank_accounts_(general)_003)
- **condition** Business savings: at least one business checking account with status OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Customer has at least one business checking account with status OPEN. (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** Business savings: fewer than 4 existing business savings accounts. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Customer has fewer than 4 existing business savings accounts. (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** Business savings: no accounts with negative balances. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Customer has no accounts with negative balances. (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** Business savings: a business checking account has been open at least 30 days. (verify: get_all_user_accounts_by_user_id_3847)  
  > - At least one existing business checking account has been open for at least 30 days. (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** Business savings: that business checking account has a current balance of at least $2,500. (verify: get_all_user_accounts_by_user_id_3847)  
  > - That business checking account has a current balance of at least $2,500. (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** Customer has confirmed the desired account_class selection. (verify: None)  
  > 3. Confirm the customer's desired account_class selection. (doc_bank_accounts_bank_accounts_(general)_001)
- **must_happen_before_this_call**: Verify customer identity.
- **must_happen_before_this_call**: Check eligibility requirements.
- **must_happen_before_this_call**: Confirm the account_class selection with the customer.
- **must_happen_after_this_call**: For savings accounts, ask the customer whether to transfer the opening deposit now; if yes transfer via transfer_funds_between_bank_accounts_7291, otherwise inform them of the 30-day funding window.
- **must_happen_after_this_call**: For business savings, ask whether to transfer the opening deposit from the qualifying business checking account now.
- **derived** `account_type`: Set to 'savings' when opening a personal savings account.
- **derived** `account_type`: Business savings doc instructs setting account_type to 'savings'.
- **derived** `account_class`: Personal checking account_class must be the full official name ending with 'Account'.
- **derived** `account_class`: Savings account_class must be the full official name ending with 'Account' exactly as confirmed with the customer.
- **derived** `account_class`: Business savings account_class is the exact official name ending with 'Account' provided by the customer.
- **derived** `user_id`: Use the authenticated customer's user identifier.

### `order_debit_card_5739`
- **call first** `get_user_information_by_id`: Verify customer identity, check date_of_birth for age 18+, and check that address on file is a valid US domestic address  
  > 7) Customer must be at least 18 years old (verify using date_of_birth) (doc_bank_accounts_bank_accounts_(general)_023)
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm account is a checking account, status OPEN, open at least 3 business days, balance at least $25, and determine account tier for fees  
  > 3) Check eligibility requirements for the specified account (doc_bank_accounts_bank_accounts_(general)_023)
- **call first** `get_debit_cards_by_account_id_7823`: Check active debit card count, pending debit card orders, and replacement history within 12 months  
  > 8) Customer cannot have a pending debit card order for the same account (check debit_cards table for PENDING status) (doc_bank_accounts_bank_accounts_(general)_023)
- **call first** `get_current_time`: Compute business days since account opening, customer age, and rolling 12-month replacement window  
  > 4) Account must have been open for at least 3 business days (excluding weekends) (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Customer identity must be verified (verify: get_user_information_by_id)  
  > 1) Customer must be verified (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Account type must be 'checking' (verify: get_all_user_accounts_by_user_id_3847)  
  > 2) The account must be a checking account (account_type must be 'checking') (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Account status must be OPEN (verify: get_all_user_accounts_by_user_id_3847)  
  > 3) Account status must be OPEN (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Account must have been open at least 3 business days excluding weekends (verify: get_all_user_accounts_by_user_id_3847)  
  > 4) Account must have been open for at least 3 business days (excluding weekends) (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** No more than 1 active debit card per checking account (verify: get_debit_cards_by_account_id_7823)  
  > 5) Customer cannot have more than 1 active debit cards per checking account (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Account balance must be at least $25 (verify: get_all_user_accounts_by_user_id_3847)  
  > 6) Account must have a minimum balance of $25 (to cover potential fees) (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Customer must be at least 18 years old based on date_of_birth (verify: get_user_information_by_id)  
  > 7) Customer must be at least 18 years old (verify using date_of_birth) (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** No PENDING debit card order for the same account (verify: get_debit_cards_by_account_id_7823)  
  > 8) Customer cannot have a pending debit card order for the same account (check debit_cards table for PENDING status) (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Customer's address on file must be a valid US domestic address (verify: get_user_information_by_id)  
  > 9) Customer's address on file must be a valid US domestic address (international shipping is not available) (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Account must have sufficient funds for delivery and design fees (verify: get_all_user_accounts_by_user_id_3847)  
  > - If the account has insufficient funds for delivery or design fees, the order will fail (doc_bank_accounts_bank_accounts_(general)_023)
- **condition** Entry tier: replacement cannot be ordered within 48 hours of card closure (verify: get_debit_cards_by_account_id_7823)  
  > - 48-hour waiting period after card closure before a replacement can be ordered (doc_bank_accounts_bank_accounts_(general)_029)
- **condition** Entry tier: only STANDARD delivery allowed (verify: get_all_user_accounts_by_user_id_3847)  
  > - Standard shipping only (no expedited option available) - delivery_fee: $0 (doc_bank_accounts_bank_accounts_(general)_029)
- **condition** Premium tier: if 5 replacements in rolling 12 months exceeded, must wait (no fee option) (verify: get_debit_cards_by_account_id_7823)  
  > - If customer has exceeded the 5-card limit, they must wait until oldest replacement ages out (no fee option - must wait) (doc_bank_accounts_bank_accounts_(general)_029)
- **condition** Customer must be informed that fees will be deducted from checking account balance before order (verify: None)  
  > Always inform the customer that the fee will be deducted from their checking account balance before placing the order. (doc_bank_accounts_bank_accounts_(general)_029)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Confirm which checking account to link
- **must_happen_before_this_call**: Check eligibility requirements
- **must_happen_before_this_call**: Ask preferred delivery option and explain fees
- **must_happen_before_this_call**: Ask preferred card design and explain fees
- **must_happen_before_this_call**: Confirm shipping address
- **must_happen_before_this_call**: Inform customer fees will be deducted from checking account
- **must_happen_after_this_call**: Inform customer of expected delivery timeframe and applicable fees
- **derived** `delivery_fee`: By tier and option: Entry STANDARD $0 only; Mid STANDARD $0, EXPEDITED $15; Premium STANDARD/EXPEDITED $0, RUSH $35; Elite all $0. Default (non-tier) STANDARD $0, EXPEDITED $15, RUSH $35
- **derived** `design_fee`: CLASSIC $0 all tiers; PREMIUM $10 Entry/Mid, $0 Premium/Elite; CUSTOM $25 Entry/Mid, $15 Premium, $0 Elite
- **derived** `excess_replacement_fee`: If replacements (issue_reason lost/stolen/fraud/damaged) in last 12 months exceed tier limit: Entry (>2) $25, Mid (>3) $15; Premium not allowed; Elite unlimited; otherwise omit/0
- **derived** `excess_replacement_fee`: Mid tier exceeding 3 replacements in rolling 12 months: $15

### `order_replacement_credit_card_7291`
- **call first** `get_credit_card_accounts_by_user`: Look up the customer's credit card account to obtain the credit_card_account_id of the card being replaced  
  > Look up the customer's credit card account. (doc_credit_cards_credit_card_replacements_001)
- **call first** `get_user_information_by_id`: Retrieve customer details (DOB, email, phone, address) to verify identity and to confirm the primary shipping address  
  > Verify the customer's identity using standard verification procedures. (doc_credit_cards_credit_card_replacements_001)
- **condition** Customer's identity has been verified using standard verification procedures (verify: get_user_information_by_id)  
  > Verify the customer's identity using standard verification procedures. (doc_credit_cards_credit_card_replacements_001)
- **condition** The credit card account being replaced belongs to the customer (looked up) (verify: get_credit_card_accounts_by_user)  
  > Look up the customer's credit card account. (doc_credit_cards_credit_card_replacements_001)
- **condition** Shipping address has been confirmed with the customer (primary or alternate, including unit/suite information) (verify: get_user_information_by_id)  
  > Confirm the shipping address with the customer (primary or alternate, including any unit or suite information). (doc_credit_cards_credit_card_replacements_001)
- **condition** Replacement reason was asked of the customer and is exactly one of fraud_suspected, lost, stolen, damaged, expired, other (verify: None)  
  > Ask for the replacement reason and record exactly one of: fraud_suspected, lost, stolen, damaged, expired, or other. (doc_credit_cards_credit_card_replacements_001)
- **condition** Customer was asked whether they want expedited shipping and advised of tier-based fees; consent captured if a fee applies (verify: get_credit_card_accounts_by_user)  
  > Ask whether they want expedited shipping (advise on possible fees by tier; see Shipping selection). (doc_credit_cards_credit_card_replacements_001)
- **condition** Customer is eligible for replacement per the knowledge base; do not unlock or call the tool otherwise (verify: None)  
  > Do not unlock or call the tool unless the customer is eligible. (doc_credit_cards_credit_card_replacements_001)
- **must_happen_before_this_call**: Unlock the tool via unlock_discoverable_agent_tool with tool_name order_replacement_credit_card_7291
- **must_happen_before_this_call**: Confirm eligibility for replacement in the knowledge base
- **must_happen_after_this_call**: Communicate the expected delivery window based on selected shipping method
- **must_happen_after_this_call**: If reason was fraud_suspected or stolen, remind customer to review recent transactions and dispute unauthorized charges
- **must_happen_after_this_call**: Document the interaction and replacement order details in the customer record
- **derived** `reason`: Must be exactly one of fraud_suspected, lost, stolen, damaged, expired, other, as stated by the customer
- **derived** `expedited_shipping`: Set per customer choice; strongly recommend true when reason is fraud_suspected or stolen; fee depends on card tier (entry $15, mid $10, premium $0) and requires consent if a fee applies

### `pay_credit_card_from_checking_9182`
- **call first** `get_user_information_by_id`: Verify the customer's identity using standard procedures before processing the payment.  
  > Verify the customer's identity using standard procedures. (doc_credit_cards_credit_card_account_logistics_009)
- **call first** `get_all_user_accounts_by_user_id_3847`: Look up the customer's Rho-Bank checking account to obtain its ID and confirm sufficient funds.  
  > Look up the customer's checking account to confirm sufficient funds. (doc_credit_cards_credit_card_account_logistics_009)
- **call first** `get_credit_card_accounts_by_user`: Look up the customer's credit card account to obtain its ID and confirm the outstanding balance.  
  > Look up the customer's credit card account to confirm the outstanding balance. (doc_credit_cards_credit_card_account_logistics_009)
- **condition** The customer's identity has been verified. (verify: get_user_information_by_id)  
  > Verify the customer's identity using standard procedures. (doc_credit_cards_credit_card_account_logistics_009)
- **condition** The customer has a Rho-Bank checking account with sufficient funds to cover the payment amount. (verify: get_all_user_accounts_by_user_id_3847)  
  > Confirm the customer has a Rho-Bank checking account with sufficient funds to cover the payment amount. (doc_credit_cards_credit_card_account_logistics_009)
- **condition** The amount must be positive and must not exceed the checking account balance or the credit card outstanding balance. (verify: get_credit_card_accounts_by_user)  
  > Must be positive and cannot exceed the checking account balance or the credit card outstanding balance. (doc_credit_cards_credit_card_account_logistics_009)
- **condition** The customer has confirmed the payment amount and authorized the transfer. (verify: None)  
  > Confirm the payment amount with the customer and obtain authorization to transfer. (doc_credit_cards_credit_card_account_logistics_009)
- **condition** The account IDs and user_id must match the authenticated customer and the amount must be authorized. (verify: get_all_user_accounts_by_user_id_3847)  
  > Then pass the arguments via call_discoverable_agent_tool exactly as listed above, ensuring the account IDs and user_id match the authenticated customer and the amount is authorized. (doc_credit_cards_credit_card_account_logistics_009)
- **must_happen_before_this_call**: Verify the customer's identity.
- **must_happen_before_this_call**: Look up the checking account to confirm sufficient funds.
- **must_happen_before_this_call**: Look up the credit card account to confirm the outstanding balance.
- **must_happen_before_this_call**: Confirm payment amount with the customer and obtain transfer authorization.
- **must_happen_before_this_call**: Unlock pay_credit_card_from_checking_9182 via unlock_discoverable_agent_tool.

### `request_temporary_debit_card_limit_increase_8374`
- **call first** `get_all_user_accounts_by_user_id_3847`: Verify the linked checking account is OPEN and at least 60 days old  
  > 1) **Account Status**: The linked checking account must be OPEN (in good standing) (doc_bank_accounts_bank_accounts_(general)_040)
- **call first** `get_bank_account_transactions_9173`: Check for overdraft fees in the last 30 days  
  > 3) **Overdraft History**: No overdraft fees in the last 30 days (doc_bank_accounts_bank_accounts_(general)_040)
- **call first** `get_debit_cards_by_account_id_7823`: Verify the debit card is ACTIVE  
  > 4) **Card Status**: The debit card must be ACTIVE (doc_bank_accounts_bank_accounts_(general)_040)
- **call first** `get_current_time`: Compute account age and the 30-day overdraft window  
  > 2) **Account Age**: The account must be at least 60 days old (doc_bank_accounts_bank_accounts_(general)_040)
- **condition** The linked checking account must be OPEN (in good standing) (verify: get_all_user_accounts_by_user_id_3847)  
  > 1) **Account Status**: The linked checking account must be OPEN (in good standing) (doc_bank_accounts_bank_accounts_(general)_040)
- **condition** The linked checking account must be at least 60 days old (verify: get_all_user_accounts_by_user_id_3847)  
  > 2) **Account Age**: The account must be at least 60 days old (doc_bank_accounts_bank_accounts_(general)_040)
- **condition** No overdraft fees on the account in the last 30 days (verify: get_bank_account_transactions_9173)  
  > 3) **Overdraft History**: No overdraft fees in the last 30 days (doc_bank_accounts_bank_accounts_(general)_040)
- **condition** The debit card must be ACTIVE (verify: get_debit_cards_by_account_id_7823)  
  > 4) **Card Status**: The debit card must be ACTIVE (doc_bank_accounts_bank_accounts_(general)_040)
- **condition** new_limit must not exceed 150% of the current limit (verify: get_debit_cards_by_account_id_7823)  
  > - **Maximum Increase**: New limit cannot exceed 150% of current limit (50% boost maximum) (doc_bank_accounts_bank_accounts_(general)_040)
- **condition** Only one temporary increase per 24-hour period per card (verify: None)  
  > - **Frequency**: Only one temporary increase per 24-hour period per card (doc_bank_accounts_bank_accounts_(general)_040)
- **must_happen_before_this_call**: Verify all eligibility requirements (account status, account age, overdraft history, card status)
- **derived** `new_limit`: Must be at most 150% of the card's current limit for the chosen limit_type

### `reset_debit_card_pin_6284`
- **call first** `get_user_information_by_id`: Retrieve customer details (date of birth, etc.) to verify identity and to check that the new PIN is not the customer's birth year or birth month/day.  
  > Verify customer identity using standard verification procedures (doc_bank_accounts_bank_accounts_(general)_027)
- **call first** `get_all_user_accounts_by_user_id_3847`: Find the customer's checking accounts so the debit card can be confirmed as belonging to the customer.  
  > Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_027)
- **call first** `get_debit_cards_by_account_id_7823`: Confirm the card belongs to the customer's account and is in ACTIVE status.  
  > Card must be in ACTIVE status (cannot change PIN on FROZEN, PENDING, or CLOSED cards) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Customer identity must be verified. (verify: get_user_information_by_id)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Customer must own the debit card (card_id belongs to one of the customer's checking accounts). (verify: get_debit_cards_by_account_id_7823)  
  > Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Debit card status must be ACTIVE (not FROZEN, PENDING, or CLOSED). (verify: get_debit_cards_by_account_id_7823)  
  > Card must be in ACTIVE status (cannot change PIN on FROZEN, PENDING, or CLOSED cards) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** Customer has confirmed the last 4 digits of their card. (verify: None)  
  > For security, ask customer to confirm the last 4 digits of their card (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** new_pin must be exactly 4 digits. (verify: None)  
  > Must be exactly 4 digits (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** new_pin cannot be sequential (e.g., 1234, 4321). (verify: None)  
  > Cannot be sequential (e.g., 1234, 4321) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** new_pin cannot be all the same digit (e.g., 1111). (verify: None)  
  > Cannot be all the same digit (e.g., 1111) (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** new_pin cannot be the customer's birth year or birth month/day. (verify: get_user_information_by_id)  
  > Cannot be the customer's birth year or birth month/day (doc_bank_accounts_bank_accounts_(general)_027)
- **condition** This tool is for customers who forgot their PIN; if the customer knows the current PIN, change_debit_card_pin_6285 is used instead. (verify: None)  
  > Use reset_debit_card_pin_6284 with parameters: card_id, last_4_digits, new_pin (doc_bank_accounts_bank_accounts_(general)_027)
- **must_happen_before_this_call**: Verify customer identity.
- **must_happen_before_this_call**: Ask customer to confirm the last 4 digits of their card.
- **must_happen_before_this_call**: Ask customer to provide a new 4-digit PIN.
- **must_happen_before_this_call**: Validate the new PIN meets security requirements.
- **must_happen_before_this_call**: If the card is frozen, it must be unfrozen first.
- **must_happen_after_this_call**: Confirm to the customer the PIN has been changed and is effective immediately (never read back the PIN).

### `set_debit_card_recurring_block_7382`
- **call first** `get_user_information_by_id`: Look up the customer's information on file so their identity can be verified before changing card settings.  
  > Verify customer identity (doc_bank_accounts_bank_accounts_(general)_034)
- **condition** The customer's identity must be verified before the recurring block is changed. (verify: get_user_information_by_id)  
  > Verify customer identity (doc_bank_accounts_bank_accounts_(general)_034)
- **condition** The customer must have been told that the block applies to ALL recurring payments on the card, not just one merchant. (verify: None)  
  > Explain that this will block ALL recurring payments on the card, not just one merchant (doc_bank_accounts_bank_accounts_(general)_034)
- **condition** If the customer only wants to block one merchant, the agent should advise them to cancel directly with that merchant instead of using the card-wide block. (verify: None)  
  > If customer only wants to block one merchant, advise them to cancel directly with that merchant (doc_bank_accounts_bank_accounts_(general)_034)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_before_this_call**: Explain to the customer that the block affects ALL recurring payments on the card
- **must_happen_before_this_call**: If the customer also needs a dispute for past charges after cancellation, file the dispute first
- **must_happen_after_this_call**: Inform the customer that the block takes effect within 24 hours
- **must_happen_after_this_call**: Inform the customer that one-time purchases are not affected
- **must_happen_after_this_call**: Inform the customer that the block does not cancel their subscriptions and they must contact merchants directly
- **must_happen_after_this_call**: Inform the customer that the block remains active until they request its removal
- **must_happen_after_this_call**: When both a dispute and a block were needed, advise the customer to confirm cancellation directly with the merchant in writing
- **derived** `block_recurring`: Set to true if the customer wants to block recurring payments; set to false if they want to unblock them.

### `submit_credit_limit_increase_request_7392`
- **call first** `get_credit_card_accounts_by_user`: Look up the credit card account and its card tier so the requested increase can be checked against the tier's maximum allowed increase before submission.  
  > BEFORE submitting any CLI request, verify that the customer's requested increase amount is within the maximum allowed for their card tier. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** The requested_increase_amount must not exceed the maximum allowed increase for the customer's card tier. (verify: get_credit_card_accounts_by_user)  
  > Do NOT submit a request that exceeds the tier limit. (doc_credit_cards_credit_card_account_logistics_007)
- **condition** The customer must have confirmed a valid increase amount within their tier's limits (if they over-requested, they must have adjusted the request). (verify: None)  
  > Once the customer has confirmed a valid increase amount within their tier's limits, submit the request on their behalf using the submit_credit_limit_increase_request_7392 tool. (doc_credit_cards_credit_card_account_logistics_007)
- **must_happen_before_this_call**: Verify the requested increase amount is within the card tier's maximum (Step 0).
- **must_happen_after_this_call**: Perform all eligibility checks (account age, cooldown via get_credit_limit_increase_history_4829, disputes, pending replacement cards, good standing, utilization).
- **must_happen_after_this_call**: Eligibility checks are performed only after the submission creates the formal record.
- **must_happen_after_this_call**: Approve via approve_credit_limit_increase_5847 or deny via deny_credit_limit_increase_5848 after eligibility checks.

### `submit_interest_discrepancy_report_7294`
- **call first** `get_all_user_accounts_by_user_id_3847`: Look up the customer's accounts to verify ownership and determine APY components (linked checking, credit cards, relationship products)  
  > 2) Look up the customer's accounts using get_all_user_accounts_by_user_id_3847 (doc_bank_accounts_bank_accounts_(general)_044)
- **call first** `get_bank_account_transactions_9173`: Find the interest credit actually applied to the savings account  
  > 3) Check transaction history using get_bank_account_transactions_9173 to find the interest credit (doc_bank_accounts_bank_accounts_(general)_044)
- **condition** Customer's identity and ownership of the savings account must be verified (verify: get_all_user_accounts_by_user_id_3847)  
  > 1) Verify the customer's identity and account ownership (doc_bank_accounts_bank_accounts_(general)_044)
- **condition** A discrepancy must exist between expected and actual interest credited (missing APY boost, incorrect tier rate, missing relationship bonus, or other calculation error) (verify: get_bank_account_transactions_9173)  
  > 4. System Calculation Error: Any other discrepancy between expected and actual interest credited. (doc_bank_accounts_bank_accounts_(general)_044)
- **condition** The account must be a savings account (verify: get_all_user_accounts_by_user_id_3847)  
  > - account_id (string): The savings account ID with the discrepancy (doc_bank_accounts_bank_accounts_(general)_044)
- **must_happen_before_this_call**: Apply a credit to the customer's savings account using apply_savings_account_credit_6831 (credit_type interest_correction)
- **must_happen_before_this_call**: Look up customer's accounts with get_all_user_accounts_by_user_id_3847
- **must_happen_before_this_call**: Check transaction history with get_bank_account_transactions_9173 to find the interest credit
- **derived** `expected_apy`: Sum of all applicable APY components (base rate, tier rate, linked checking boost, credit card bonuses, relationship bonus) per the savings account type documentation
- **derived** `amount_difference`: Expected interest minus actual interest credited (as found in transaction history)

### `transfer_funds_between_bank_accounts_7291`
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm that the source and destination accounts exist, belong to the same customer, are ACTIVE/OPEN, and that the source has enough funds for the transfer.  
  > Confirm both the source and destination accounts are in ACTIVE or OPEN status (doc_bank_accounts_bank_accounts_(general)_010)
- **condition** Both the source and destination accounts must be in ACTIVE or OPEN status. (verify: get_all_user_accounts_by_user_id_3847)  
  > Requirements: Both the source and destination accounts must be in ACTIVE or OPEN status. (doc_bank_accounts_bank_accounts_(general)_010)
- **condition** The source account must have sufficient available funds to cover the transfer amount. (verify: get_all_user_accounts_by_user_id_3847)  
  > Verify the source account has sufficient available funds to cover the transfer amount (doc_bank_accounts_bank_accounts_(general)_010)
- **condition** Both accounts must belong to the same customer, and the customer must have authorized the transfer. (verify: get_all_user_accounts_by_user_id_3847)  
  > Ensure the two accounts belong to the same customer and the customer has authorized the transfer (doc_bank_accounts_bank_accounts_(general)_010)
- **condition** The amount must be a positive USD value. (verify: None)  
  > Validate the amount is a positive USD value (doc_bank_accounts_bank_accounts_(general)_010)
- **condition** The source and destination account IDs must be distinct and valid. (verify: get_all_user_accounts_by_user_id_3847)  
  > Confirm the source and destination account IDs are distinct and valid (doc_bank_accounts_bank_accounts_(general)_010)
- **condition** For a savings opening deposit, the customer must authorize an immediate transfer. (verify: None)  
  >   - When to call: In step 5, only if the customer authorizes an immediate transfer for the opening deposit. (doc_bank_accounts_bank_accounts_(general)_002)
- **condition** For a business savings opening deposit, the source must be an OPEN business checking account that has been open at least 30 days and holds a balance of at least $2,500. (verify: get_all_user_accounts_by_user_id_3847)  
  > - Use the qualifying OPEN business checking account that meets both the tenure and balance thresholds as the source for the optional opening deposit transfer. (doc_bank_accounts_bank_accounts_(general)_004)
- **condition** For a business savings opening deposit, the customer must authorize transferring the deposit now. (verify: None)  
  >   - Only if the customer authorizes transferring the opening deposit now. (doc_bank_accounts_bank_accounts_(general)_004)
- **must_happen_before_this_call**: Open the new savings account with open_bank_account_4821 (opening deposit case).
- **must_happen_before_this_call**: Verify the customer's identity.
- **must_happen_before_this_call**: Validate account statuses and available funds.
- **must_happen_after_this_call**: Verify the transfer posted as expected and that no duplicate transfer was initiated.
- **must_happen_after_this_call**: Confirm completion to the customer and document the action.
- **derived** `source_account_id`: For a personal savings opening deposit, use the customer's Rho-Bank checking account.
- **derived** `destination_account_id`: For a personal savings opening deposit, use the newly opened savings account.
- **derived** `amount`: For an opening deposit, use the required opening deposit amount confirmed with the customer.
- **derived** `source_account_id`: For a business savings opening deposit, use the qualifying OPEN business checking account (open at least 30 days, balance of at least $2,500).
- **derived** `destination_account_id`: For a business savings opening deposit, use the newly opened business savings account_id.

### `unfreeze_debit_card_3893`
- **call first** `get_all_user_accounts_by_user_id_3847`: Confirm the customer owns the checking account linked to the debit card, and that this linked checking account is still OPEN.  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_026)
- **call first** `get_debit_cards_by_account_id_7823`: Confirm the debit card belongs to the customer's checking account and is currently in FROZEN status.  
  > Card must currently be in FROZEN status (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Customer identity must be verified. (verify: get_user_information_by_id)  
  > Customer must be verified (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Customer must be the owner of the debit card (the card is linked to one of the customer's checking accounts). (verify: get_debit_cards_by_account_id_7823)  
  > Customer must be the owner of the debit card (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** Debit card status must currently be FROZEN. (verify: get_debit_cards_by_account_id_7823)  
  > Card must currently be in FROZEN status (doc_bank_accounts_bank_accounts_(general)_026)
- **condition** The checking account linked to the card must be OPEN. (verify: get_all_user_accounts_by_user_id_3847)  
  > The linked checking account must still be OPEN (doc_bank_accounts_bank_accounts_(general)_026)
- **must_happen_before_this_call**: Verify customer identity
- **must_happen_after_this_call**: Confirm to the customer that the card is now active and ready to use immediately.

### `update_transaction_rewards_3847`
- **call first** `get_credit_card_accounts_by_user`: Determine the card type needed to recalculate the correct rewards rate.  
  > Recalculate the correct rewards for each transaction based on the card type, transaction category, and any applicable promotions. (doc_credit_cards_credit_cards_(general)_004)
- **call first** `get_credit_card_transactions_by_user`: Retrieve the transaction's category, amount, and date to independently recalculate rewards.  
  > Recalculate the correct rewards for each transaction based on the card type, transaction category, and any applicable promotions. (doc_credit_cards_credit_cards_(general)_004)
- **condition** The cash back dispute for the transaction has been resolved and approved. (verify: None)  
  > After a cash back dispute is resolved and approved, you must update the affected transaction(s) with the correct rewards value. (doc_credit_cards_credit_cards_(general)_004)
- **condition** The transaction_id comes from the user's resolved disputes in the cash_back_disputes database. (verify: None)  
  > Look up the user’s resolved disputes in the cash_back_disputes database to find the transaction_id values that need rewards adjustments. (doc_credit_cards_credit_cards_(general)_004)
- **condition** The tool update_transaction_rewards_3847 has been unlocked. (verify: list_discoverable_agent_tools)  
  > Use `unlock_discoverable_agent_tool` to unlock the agent tool `update_transaction_rewards_3847`. (doc_credit_cards_credit_cards_(general)_004)
- **condition** The rewards value must be independently verified, not taken from the dispute record's expected_rewards field. (verify: None)  
  > Important: Do not rely on any expected_rewards field in the dispute record. (doc_credit_cards_credit_cards_(general)_004)
- **condition** The calculation reflects the proper base rate and any bonus category or promotion active at the time of purchase. (verify: get_credit_card_transactions_by_user)  
  > Ensure your calculation reflects the proper base rate and any active bonus category or promotion at the time of purchase. (doc_credit_cards_credit_cards_(general)_004)
- **must_happen_before_this_call**: Look up the user's resolved cash back disputes to identify the transaction_ids.
- **must_happen_before_this_call**: Unlock update_transaction_rewards_3847.
- **must_happen_before_this_call**: Recalculate the correct rewards for each transaction.
- **must_happen_after_this_call**: Confirm the update in credit_card_transaction_history.
- **must_happen_after_this_call**: Retain calculation notes in the internal case record.
- **derived** `new_rewards_earned`: String formatted as 'X points', where X is the whole-number point value recalculated from the card type, transaction category, base rate, and promotions active at purchase time (not from expected_rewards).
- **derived** `transaction_id`: The exact transaction identifier from the user's resolved cash back dispute.
