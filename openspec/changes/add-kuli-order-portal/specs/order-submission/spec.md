## ADDED Requirements

### Requirement: Note form collects demand details
The system SHALL provide a "写小纸条" submission form that collects demand description, service category, urgency, budget preference, contact information, and optional remote-help preference.

#### Scenario: Visitor sees note form
- **WHEN** a visitor opens the note page
- **THEN** the form includes demand description, service category, urgency, budget, and contact fields

#### Scenario: Demand character count updates
- **WHEN** a visitor types in the demand description
- **THEN** the page shows an updated character count with an 800 character limit

### Requirement: Note form validates required fields
The system SHALL reject submissions that omit required demand description or contact information.

#### Scenario: Missing demand
- **WHEN** a visitor submits the note form without demand description
- **THEN** the system shows a visible validation message and does not create an order

#### Scenario: Missing contact
- **WHEN** a visitor submits the note form without contact information
- **THEN** the system shows a visible validation message and does not create an order

### Requirement: Public inquiries can be created
The system SHALL allow unauthenticated visitors to submit public inquiries that are visible to administrators.

#### Scenario: Visitor submits valid note
- **WHEN** an unauthenticated visitor submits a valid note
- **THEN** the backend creates an inquiry with a unique order number, initial status, and no normal-account ownership

#### Scenario: Visitor receives submission result
- **WHEN** a public inquiry is created
- **THEN** the frontend shows a success state with the generated order number and explains that login is required for progress tracking

### Requirement: Logged-in users can create owned orders
The system SHALL allow authenticated normal accounts to create account-owned orders from the note form.

#### Scenario: Normal account submits valid order
- **WHEN** a logged-in normal account submits a valid note
- **THEN** the backend creates an order linked to that account with a unique order number and initial status

#### Scenario: Created order appears in account view
- **WHEN** a normal account creates an owned order
- **THEN** the order appears in that account's order progress view
