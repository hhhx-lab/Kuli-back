## ADDED Requirements

### Requirement: Normal accounts see their own orders
The system SHALL allow normal accounts to view only their own account-owned orders.

#### Scenario: Normal account lists orders
- **WHEN** a normal account opens the orders page
- **THEN** the frontend shows only orders owned by that account

#### Scenario: Normal account opens owned order
- **WHEN** a normal account opens one of its own orders
- **THEN** the page shows order number, demand summary, quoted price, current progress, public notes, messages, and attachment status

### Requirement: Normal accounts cannot see internal fields
The system SHALL hide internal business fields from normal accounts.

#### Scenario: Normal account reads order response
- **WHEN** a normal account fetches an owned order
- **THEN** the response does not include cost, profit, internal priority, or internal notes

### Requirement: Normal accounts cannot access other orders
The system SHALL prevent normal accounts from viewing orders owned by other accounts or public unowned inquiries.

#### Scenario: Normal account changes order id
- **WHEN** a normal account requests another account's order by id or order number
- **THEN** the backend rejects the request

#### Scenario: Unauthenticated visitor opens order detail
- **WHEN** an unauthenticated visitor attempts to open an order detail route
- **THEN** the frontend or backend requires login before showing any order details

### Requirement: Progress stages are consistent
The system SHALL use consistent progress states across list and detail views.

#### Scenario: Order status changes
- **WHEN** an order status is updated by an admin
- **THEN** the normal account list and detail views show the same updated progress stage
