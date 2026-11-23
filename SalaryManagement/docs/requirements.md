
# Salary Management — Requirements

## 1. Goal

Build a centralized employee and salary management application for ACME, replacing spreadsheet-based HR management with a reliable, searchable, and analytics-driven system.

The application must enable HR to manage employee records and understand salary distribution and payroll costs across countries, departments, and job titles.

## 2. Users

**Primary user: HR Manager**

The HR Manager is responsible for:
- Managing employee information.
- Viewing and updating employee salaries.
- Reviewing historical salary changes.
- Understanding organizational salary distribution.
- Identifying unusually high or low salaries.
- Monitoring total annual payroll costs.

Authentication and role management are excluded from the assessment scope because there is only one user persona.

## 3. In Scope

### Employee management
- Create, view, update, search, filter, sort, and delete employees.
- Support server-side pagination.
- Store employee details including name, email, job title, department, country, employment type, and hire date.
- Display the employee's current salary.

### Salary management
- Record annual gross salaries in the employee's local currency.
- Maintain append-only salary history.
- Add new salary records without overwriting previous records.
- Display salary history on the employee detail page.
- Show local salary amounts and their USD equivalents.

### Salary analytics
- Calculate salary statistics grouped by country, department, or job title.
- Report count, minimum, 25th percentile, median, 75th percentile, maximum, and average salary.
- Show total annual payroll, headcount, average salary, and median salary.
- Display salary distribution using histogram buckets.
- Identify salary outliers within job-title groups.

### Currency handling
- Use USD as the base currency.
- Maintain static exchange rates in the database.
- Convert international salary amounts before performing cross-country comparisons.
- Use decimal-based monetary values rather than floating-point values.

### Data and infrastructure
- Use PostgreSQL for persistent storage.
- Include database migrations.
- Provide a deterministic seed script that creates exactly 10,000 employees.
- Include automated backend and frontend tests.
- Provide Docker-based local infrastructure.
- Document deployment and setup instructions.

## 4. Deliberately Out of Scope

| Feature | Reason |
|---|---|
| Authentication and RBAC | Only one HR Manager persona is required. |
| Approval workflows | Salary approval processes are not part of the core assessment. |
| Payroll and tax calculations | The application manages salary information, not payroll execution. |
| Live exchange rates | Static seeded rates keep results deterministic and avoid external dependencies. |
| Bonuses, equity, and benefits | The initial domain model focuses on annual gross salary. |
| Multi-tenancy | Only one ACME organization is being modeled. |
| Audit logs | Historical salary changes are retained, but a complete audit system is unnecessary for this scope. |

## 5. Assumptions

- The system manages approximately 10,000 employees across multiple countries.
- Salary values represent annual gross compensation in local currency.
- USD is the base currency for international comparisons.
- Exchange rates are static and stored in the database.
- The current salary is the salary record with the latest effective date.
- Seeded employee records are synthetic and reproducible using a fixed random seed.
- All salary calculations use decimal arithmetic.
- PostgreSQL performs filtering, sorting, pagination, grouping, and percentile calculations.
- The HR Manager uses the application through a web interface.

## 6. Success Criteria

The project is successful when:

1. The HR Manager can complete employee CRUD operations through the frontend.
2. Employee records support search, filtering, sorting, and server-side pagination.
3. Salary changes preserve previous salary records.
4. Salary comparisons across countries are correctly converted into USD.
5. The analytics dashboard provides the required statistics and visualizations.
6. The outlier endpoint identifies unusual salaries within peer groups.
7. The seed script creates exactly 10,000 deterministic employee records.
8. Automated tests cover important business rules, API behavior, and frontend interactions.
9. The application can be started locally using documented instructions.
10. The application can be deployed and accessed through a live URL.
