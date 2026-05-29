## ADDED Requirements

### Requirement: Reserved project portal is visible
The system SHALL include a visible reserved entry for future project or subproduct management.

#### Scenario: User opens portal page
- **WHEN** a visitor, normal account, or admin opens the reserved portal page
- **THEN** the page explains that project management is reserved for a later change

### Requirement: Reserved portal has no filesystem access
The system SHALL NOT read, list, index, or expose local project directories for the reserved portal in this change.

#### Scenario: Portal page loads
- **WHEN** the reserved portal page loads
- **THEN** no API request or backend handler reads `/Users/hwaigc/太空垃圾站` or other local filesystem project directories

### Requirement: Reserved portal is excluded from admin authority
The system SHALL NOT grant administrators subproject management ability in this change.

#### Scenario: Admin opens portal page
- **WHEN** an admin opens the reserved project portal
- **THEN** the page remains a placeholder and does not show project management controls
