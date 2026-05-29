## ADDED Requirements

### Requirement: Email password authentication
The system SHALL authenticate users with email and password.

#### Scenario: Successful login
- **WHEN** a user submits a registered email and correct password
- **THEN** the backend returns an authenticated session token and the user's role

#### Scenario: Failed login
- **WHEN** a user submits an unknown email or wrong password
- **THEN** the backend returns a failure response that does not reveal whether the email exists

### Requirement: Passwords are not stored in plaintext
The system SHALL store password verifiers using salted hashing rather than plaintext passwords.

#### Scenario: Seeded user exists
- **WHEN** the backend seeds a demo account
- **THEN** the stored password field is a salted hash and not the original password

### Requirement: Roles are enforced server-side
The system SHALL distinguish `admin` and `user` accounts in API authorization.

#### Scenario: Admin accesses admin API
- **WHEN** an authenticated admin account calls an admin-only endpoint
- **THEN** the backend allows the request

#### Scenario: Normal account accesses admin API
- **WHEN** an authenticated normal account calls an admin-only endpoint
- **THEN** the backend rejects the request

#### Scenario: Unauthenticated request accesses protected API
- **WHEN** a request without a valid token calls a protected endpoint
- **THEN** the backend rejects the request

### Requirement: Role cannot be escalated by client input
The system SHALL ignore client-controlled role or owner fields when authorizing order access.

#### Scenario: Normal account sends admin-like request
- **WHEN** a normal account sends request parameters claiming admin role or another owner id
- **THEN** the backend still authorizes based on the authenticated token and stored account role
