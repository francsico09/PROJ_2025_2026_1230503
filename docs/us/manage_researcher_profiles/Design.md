
# Manage Researcher Profiles

## Context

**US:** As an administrator I want to manage researcher profiles so 
that I can correctly manage researcher users inside the platform and the
extraction of metrics related to them.
I want to be able to associate new profiles to existing users, update
existing profiles, including extracting metrics for them, and delete
researcher profiles when necessary.

## Design

### Domain Classes

- **ResearcherProfile**
    - Represents the researcher profile associated to users of the 
  system.
    - Contains the associated metrics.
  
- **ResearcherMetric**
    - Represents the metrics associated to a researcher profile.
    - Contains the data related to the researcher's performance and 
  impact.
    - Can be extracted of various sources.

### Controller
- **ResearcherProfileController**
    - Handles the input from the user interface.
    - Invokes the application service to execute the use case.
    - Returns the response (success or validation errors) to the UI layer.

###  Repository
- **PostgresResearcherProfileRepository**
    - Provides access to persisted `ResearcherProfile` entities.
    - Responsible for checking uniqueness and saving new researcher 
  metrics.

### Realization
The CRUD operations for researcher profiles follow the same 
architectural pattern as the User entity. Therefore, the realization
of the use case is based on the same principles and design decisions
as the user management use case.

### Tests

Include here the main tests used to validate the functionality. Focus on how they relate to the acceptance criteria. May be automated or manual tests.

**Test 1:** *Verifies that it is not possible to ...*

```
@Test(expected = IllegalArgumentException.class)
public void ensureXxxxYyyy() {
	...
}
````

## Observations

*This section should be used to include any content that does not fit any of the previous sections.*

*The team should present here, for instance, a critical prespective on the developed work including the analysis of alternative solutioons or related works*

*The team should include in this section statements/references regarding third party works that were used in the development this work.*
