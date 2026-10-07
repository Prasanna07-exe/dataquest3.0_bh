# DQBH Roles & Permissions

## Roles

1. CUSTOMER
2. TECHNICIAN
3. MANAGER
4. INVENTORY_MANAGER
5. ADMIN

---

# CUSTOMER

Can:

- View authorized customer sites
- View authorized machines
- Create service requests
- Upload request attachments
- View own requests
- View request status
- View machine service history
- View completion reports
- Approve completion where required

Cannot:

- Assign technicians
- Modify inventory
- Approve operational plans
- Reassign technicians
- Modify system configuration

---

# TECHNICIAN

Can:

- View assigned jobs
- Accept assigned jobs
- Check in
- Start work
- Complete safety checklist
- Complete service checklist
- Add diagnosis
- Add work logs
- Record measurements
- Record consumed parts
- Upload evidence
- Submit completion
- Raise blocked/exception events
- Use authorized troubleshooting assistance

Cannot:

- Assign themselves arbitrary jobs
- Approve service plans
- Modify inventory balances directly
- Approve reassignment
- Modify authorization rules

---

# MANAGER

Can:

- View operational command center
- View service requests
- Review AI recommendations
- Review SLA risk
- Review resource feasibility
- Approve/reject requests
- Approve/reject reassignment
- Reassign technicians
- View exceptions
- View operational analytics
- View service history
- Use operations copilot

Cannot:

- Bypass authorization controls
- Directly modify inventory quantities without inventory workflow
- Execute arbitrary SQL

---

# INVENTORY_MANAGER

Can:

- View warehouses
- View inventory
- View reservations
- Reserve parts
- Manage stock
- Create transfers
- Resolve shortages
- View reorder alerts
- View part consumption

Cannot:

- Approve service requests unless explicitly authorized
- Assign technicians
- Modify customer records outside permitted scope

---

# ADMIN

Can:

- Manage users
- Manage roles
- Manage permissions
- Manage master data
- Manage system configuration
- View audit logs
- Manage integrations

Admin actions must still be audited.

---

# Security Principles

Every API request must enforce:

1. Authentication
2. Role authorization
3. Object-level authorization
4. Customer/site scope
5. State-transition rules

AI recommendations never bypass authorization.