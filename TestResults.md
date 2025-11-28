# UnitTest — Test results summary

This table summarizes each UnitTest audit log (testcase → role → access type → system criticality → gatekeeper decision → net risk score). Open any testcase for full details.

| Testcase | Role (job_title) | Access Type | System Criticality | Decision | Net Risk Score |
|---|---|---|---:|---|---:|
| [REQ-TC01](UnitTest/Audit_Log_REQ-TC01.md) | DevOps Engineer | read | non_prod | AUTO_APPROVE | 50 |
| [REQ-TC02](UnitTest/Audit_Log_REQ-TC02.md) | Data Analyst | read | non_prod | AUTO_APPROVE | 50 |
| [REQ-TC03](UnitTest/Audit_Log_REQ-TC03.md) | CI/CD Pipeline | read | non_prod | AUTO_APPROVE | 40 |
| [REQ-TC04](UnitTest/Audit_Log_REQ-TC04.md) | Catalog Agent | read | external | AUTO_APPROVE | 40 |
| [REQ-TC05](UnitTest/Audit_Log_REQ-TC05.md) | Application Developer | read | non_prod | AUTO_APPROVE | 50 |
| [REQ-TC06](UnitTest/Audit_Log_REQ-TC06.md) | Software Engineer | read_write | non_prod | AUTO_APPROVE | 60 |
| [REQ-TC07](UnitTest/Audit_Log_REQ-TC07.md) | Summer Intern | read | saas_internal | AUTO_APPROVE | 40 |
| [REQ-TC08](UnitTest/Audit_Log_REQ-TC08.md) | Key Rotation Service | execute (key rotation) | (see file) | PENDING_MANAGER_REVIEW | 80 |
| [REQ-TC09](UnitTest/Audit_Log_REQ-TC09.md) | Data Scientist | read | prod | AUTO_APPROVE | 40 |
| [REQ-TC10](UnitTest/Audit_Log_REQ-TC10.md) | ML Engineer | read_write | non_prod | AUTO_APPROVE | 60 |
| [REQ-TC11](UnitTest/Audit_Log_REQ-TC11.md) | Finance Automation Agent | write | prod | PENDING_HUMAN_REVIEW | 80 |
| [REQ-TC12](UnitTest/Audit_Log_REQ-TC12.md) | Senior DevOps Engineer | admin | prod | DENY | 95 |
| [REQ-TC13](UnitTest/Audit_Log_REQ-TC13.md) | Automation Bot | admin | prod | DENY | 95 |
| [REQ-TC14](UnitTest/Audit_Log_REQ-TC14.md) | Senior Data Scientist | read | prod | AUTO_APPROVE | 50 |
| [REQ-TC15](UnitTest/Audit_Log_REQ-TC15.md) | Network Helper Agent | admin | prod | DENY | 95 |
| [REQ-TC16](UnitTest/Audit_Log_REQ-TC16.md) | Backend Developer | admin | prod | DENY | 95 |
| [REQ-TC17](UnitTest/Audit_Log_REQ-TC17.md) | RPA Bot | write | prod | AUTO_APPROVE | 55 |
| [REQ-TC18](UnitTest/Audit_Log_REQ-TC18.md) | FinTech Integration Service | write | prod | PENDING_HUMAN_REVIEW | 80 |
| [REQ-TC19](UnitTest/Audit_Log_REQ-TC19.md) | Cross-Account Orchestration Agent | admin | prod | AUTO_APPROVE | 60 |
| [REQ-TC20](UnitTest/Audit_Log_REQ-TC20.md) | CI/CD Pipeline (prod) | write | prod | PENDING_HUMAN_REVIEW | 80 |
| [REQ-TC21](UnitTest/Audit_Log_REQ-TC21.md) | Self-Directed AI Agent | admin | prod | DENY | 95 |
| [REQ-TC22](UnitTest/Audit_Log_REQ-TC22.md) | Operations Analyst | write | prod | PENDING_MANAGER_REVIEW | 80 |
| [REQ-TC23](UnitTest/Audit_Log_REQ-TC23.md) | Application Developer | admin | prod | DENY | 95 |
| [REQ-TC24](UnitTest/Audit_Log_REQ-TC24.md) | Vendor Bot | read | prod | PENDING_HUMAN_REVIEW | 70 |
| [REQ-TC25](UnitTest/Audit_Log_REQ-TC25.md) | Permissions Tuning Agent | admin | prod | DENY | 95 |
| [REQ-TC26](UnitTest/Audit_Log_REQ-TC26.md) | AI Assistant | admin | prod | DENY | 100 |
| [REQ-TC27](UnitTest/Audit_Log_REQ-TC27.md) | Business User | read | prod | AUTO_APPROVE | 40 |
| [REQ-TC28](UnitTest/Audit_Log_REQ-TC28.md) | On-Call Engineer | admin | prod | DENY | 95 |
| [REQ-TC29](UnitTest/Audit_Log_REQ-TC29.md) | AI Troubleshooter | admin | prod | DENY | 95 |
| [REQ-TC30](UnitTest/Audit_Log_REQ-TC30.md) | Power User| admin | prod | DENY | 95 |

> Notes:
> - All testcase files are available in UnitTest/ — open any link to inspect full JSON audit logs.
> - Fields marked “(see file)” were not available in the provided excerpts; open the file to confirm.
