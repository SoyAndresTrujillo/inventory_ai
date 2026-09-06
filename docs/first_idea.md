# Inventory + AI

## Context

The inventory software market is heavily saturated with countless solutions. Our goal is to automate the manual processes these systems still rely on, using artificial intelligence.

We want the full inventory management lifecycle to be automated:

- Product intake (stock in)
- Product dispatch (stock out)
- Invoices
- Payments
- Reports
- Payment reminders

## Scope (MVP)

### 1. Products module

- Create products.
- Products are related to categories, so a **Categories module** is required.
- Categories are created first and then displayed during product creation.
- Categories cover any attribute that describes a product — for example `Country`, `State`, `City`, and others.
- The module also allows creating **templates** to speed up future product creation.

### 2. AI module

A chat interface where the user can **create, update, and delete products** — one at a time or in bulk.

**Supported input types:**

- Text
- Audio
- Photos
- XML files
- JSON files
- Excel files

**Expected behavior:**

1. Read the information the user provides.
2. Ask follow-up questions when data is missing or ambiguous.
3. Infer the user's intent and call the corresponding APIs.
4. Return a summary report of the operation, detailing what was created, updated, or deleted.

Scope of the AI module is limited to product creation, update, and deletion.

## Design

- **Colors:** not defined yet — strategic colors may be chosen freely.
- **UI:** slightly rounded borders, clean and uncluttered.
- **UX:** keep flows short. Do not overload the user with steps, while still covering everything defined in the scope.