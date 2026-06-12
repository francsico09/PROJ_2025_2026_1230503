
# Export Researcher Metrics

## Context

**US:** As a researcher I want to export my individual metrics, with 
different levels of aggregation (total history, date range, most recent),
to XLSX or CSV file.

**US:** As an administrator I want to export data from a specific
researcher,  with different levels of aggregation (total history, date
range, most recent), to XLSX or CSV file.

**US:** As an administrator I want to export data from every researcher,
with different levels of aggregation (total history, date range, most 
recent), to XLSX or CSV file.

## Design

### Domain Classes
- **ResearcherMetric**
    - Represents the metrics associated to a researcher profile.
    - Contains the data related to the researcher's performance and
    impact.
    - Can be extracted of various sources.

### Controller
- **ExportController**
    - Handles the input from the user interface.
    - Invokes the application service to execute the use case.
    - Returns the response (success or validation errors) to the UI layer.

###  Repository
- **PostgresMetricsRepository**
    - Provides access to persisted `ResearcherMetric` entities.
    - Responsible for checking uniqueness and saving new users.

### Realization

#### SSD's

#### SD's

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
