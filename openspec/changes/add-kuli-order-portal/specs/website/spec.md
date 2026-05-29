## ADDED Requirements

### Requirement: Public homepage and navigation
The system SHALL provide a Kuli public website with routes or pages for homepage, services, writing a note, order access, admin access, and reserved project portal.

#### Scenario: Visitor opens the homepage
- **WHEN** a visitor opens the homepage
- **THEN** the page shows the Kuli brand, team positioning, primary service categories, a note submission CTA, and navigation to services and writing a note

#### Scenario: Navigation shows current location
- **WHEN** a visitor navigates between homepage, services, and note pages
- **THEN** the current page is visually indicated and navigation links remain usable on desktop and mobile

### Requirement: Services explanation and rules
The system SHALL explain Kuli's service categories, common cases, settlement rules, FAQ, and default maintenance boundaries.

#### Scenario: Visitor views services
- **WHEN** a visitor opens the services page
- **THEN** the page includes document processing, AI tools/accounts/API, small tools/development, and deployment/configuration categories

#### Scenario: Visitor filters FAQ
- **WHEN** a visitor selects an FAQ category such as payment, scope, delivery, or risk
- **THEN** only matching FAQ entries are shown while the selected category is indicated

### Requirement: Responsive Kuli visual direction
The system SHALL preserve the Kuli dark-window visual direction from the supplied prototype while avoiding broken resources.

#### Scenario: Mobile visitor sees CTA
- **WHEN** a visitor uses a narrow mobile viewport
- **THEN** a prominent bottom note-submission CTA is available without obscuring primary content

#### Scenario: Resources load
- **WHEN** the website is loaded in a browser
- **THEN** core CSS, JavaScript, route links, icons, and visual assets load without missing `assets/...` references

### Requirement: Reserved project portal placeholder
The system SHALL expose a reserved project/subproduct portal entry without implementing real project management.

#### Scenario: Visitor opens reserved portal
- **WHEN** a visitor opens the reserved project portal
- **THEN** the page states that subproject management is reserved and not connected yet

#### Scenario: Portal does not read local projects
- **WHEN** the reserved project portal is opened
- **THEN** the system does not read `/Users/hwaigc/太空垃圾站` or any other local project directory
