## ADDED Requirements

### Requirement: Admin can view all orders
The system SHALL allow admin accounts to list all public inquiries and account-owned orders.

#### Scenario: Admin opens dashboard
- **WHEN** an admin opens the admin dashboard
- **THEN** the frontend shows aggregate counts and a list of all orders regardless of owner

### Requirement: Admin can inspect full order details
The system SHALL allow admin accounts to view all public and internal order fields.

#### Scenario: Admin opens order detail
- **WHEN** an admin selects an order
- **THEN** the admin view shows customer id, contact, demand, quoted price, cost, profit, progress, priority, public notes, and internal notes

### Requirement: Admin can update order management fields
The system SHALL allow admin accounts to update status, priority, quoted price, cost, profit, public notes, and internal notes.

#### Scenario: Admin updates order financial fields
- **WHEN** an admin changes quoted price, cost, or profit
- **THEN** the backend persists the changes and the dashboard reflects the updated values

#### Scenario: Admin updates order status
- **WHEN** an admin changes an order status
- **THEN** the backend persists the status and customer-facing views show the updated progress

### Requirement: Admin can identify ownership
The system SHALL show whether an order belongs to a normal account or is a public inquiry.

#### Scenario: Admin views mixed orders
- **WHEN** an admin lists orders containing owned and public inquiries
- **THEN** each order indicates its owner account or public inquiry status
