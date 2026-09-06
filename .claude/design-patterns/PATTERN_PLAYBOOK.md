# Conexis Pattern Playbook

> **For agents and skills.** When writing code in Conexis, consult this doc to pick the sanctioned design pattern per layer. Each pattern links to its full explainer under `.claude/design-patterns/<pattern>/README.md`.

This is **not** a refactor plan. This is a **decision guide** for new code or local cleanup.

---

## How to use

1. **Identify your layer**: architecture / backend / frontend / database / lambda.
2. **Find the trigger** that matches what you're about to write (a smell or a need).
3. **Apply the listed pattern** and read its explainer doc.
4. **Respect guardrails** (memory anchors) — they override pattern choice.
5. If no listed pattern fits → reuse-first → only then propose a new pattern (memory: [[feedback_reuse_first_and_patterns]]).

For reverse lookup ("I see code smell X, which pattern fixes it?") → jump to **Smell Index** at end.

---

## Global guardrails (apply to all layers)

| Rule | Memory anchor | What it constrains |
|---|---|---|
| No `if (tenantId === N)` / `if (buyer.name === 'X')` — route via `permissions.<flag>` | [[feedback_no_hardcode_tenant_buyer]] | Strategy classes must be selected by flag, not by tenant name |
| Tenant FK column varies: `jobs.id_tenant` vs `contracts.tenant_id` — verify model first | [[feedback_verify_column_names]] | Repository/Proxy implementations must read column name from model metadata |
| Stay inside the stated scope; never touch unrelated modules | [[feedback_scope_discipline]] | Don't extract cross-domain abstractions on the side; flag and stop |
| Reuse-first → named pattern → DRY rule of three (extract on 3rd duplication, not 1st) | [[feedback_reuse_first_and_patterns]] | Don't create a pattern wrapper for 2 use sites |
| Tenant-scoped spec fields gated by flag, never global on shared templates | [[feedback_tenant_scoped_template_changes]] | Email/job/contract templates: branch via flag, not by inlining tenant-specific UI |
| Never use `any` / `unknown` casts; extend interfaces | CLAUDE.md §2a | Strategy/Adapter/Facade interfaces must be typed end-to-end |

---

## 1. Architecture (cross-cutting)

Cross-cutting concerns: DI, guards, permission resolution, shared services.

### Sanctioned patterns

| Trigger | Pattern | Doc | Notes |
|---|---|---|---|
| Multiple checks running in fixed order, each can short-circuit | **Chain of Responsibility** | [chain-of-responsibility](./chain-of-responsibility/README.md) | Already used by NestJS guard pipeline. Extend for new gating layers. |
| Many call sites resolving permissions/tenant metadata | **Facade** | [facade](./facade/README.md) | `TenantMetadataService` already facade-shaped. Add one entry point per concern; don't sprinkle resolver calls. |
| Service shared app-wide, single instance | **Singleton** | [singleton/README.md](./singleton/README.md) | NestJS providers are singleton by default. Validates existing choice; no extra work. |
| Tenant/buyer behavior selected by `permissions.<flag>` | **Strategy** (flag-axis) | [strategy](./strategy/README.md) | One strategy per behavior axis, not per tenant. Composable. Respect [[feedback_no_hardcode_tenant_buyer]]. |

### Patterns to avoid at this layer
- **Bridge** for tenant × role today — only justified if >1 resolver implementation exists. Defer until a DB-backed or remote permission resolver appears.

### Anchors
- DI: `back/conexis/src/app.module.ts`, `back/conexis/src/common/common.module.ts`
- Guards: `back/conexis/src/common/guards/{jwtAuth,roles,permissions}.guard.ts`
- Permission resolvers: `back/conexis/src/common/constants/tenant-metadata.constants.ts`, `back/conexis/src/common/constants/tenantRolePermissions.constants.ts`
- Cross-cutting services: `back/conexis/src/common/services/{tenant-metadata,fileGenerator,inMemoryCache,simpleEmail,simpleQueue,simpleStorage}.service.ts`

---

## 2. Backend (NestJS, 28 modules)

### Sanctioned patterns

| Trigger | Pattern | Doc | Notes |
|---|---|---|---|
| Entity has lifecycle (status: Draft → Approved → Active → …) with state-dependent methods | **State** | [state](./state/README.md) | Encapsulate transitions per state class. Removes status `if`-chains. Applies to: Contracts, Submissions, T&E. |
| `if (buyer?.X)` / `if (tenant?.X)` chains selecting algorithm variants | **Strategy** (flag-axis) | [strategy](./strategy/README.md) | One strategy per behavior axis. Selected via `permissions.<flag>` — memory: [[feedback_no_hardcode_tenant_buyer]]. |
| Service file growing >2k lines, mixing CRUD + workflow + notifications + imports | **Facade** (split) | [facade](./facade/README.md) | Break into focused facades: `<Domain>CrudFacade`, `<Domain>ApprovalFacade`, etc. Each wraps one subsystem. |
| Async work dispatched via SQS to Lambda | **Command** | [command](./command/README.md) | Model SQS messages as Command classes with `execute()` + serializable payload. Share the class with the consuming Lambda (see Lambda §5). |
| Email/PDF/document templates picked by kind | **Factory Method** | [factory-method](./factory-method/README.md) | `EmailTemplateFactory.create(kind, ctx)` returning a typed template object. Replace static helper sprawl. |
| Workflow skeleton shared across domains (validate → transition → persist → notify → audit) | **Template Method** | [template-method](./template-method/README.md) | Abstract base in `common/`, domain subclasses override only domain-specific steps. Watch [[feedback_scope_discipline]] — only extract when refactoring is sanctioned. |
| AI agent / external service orchestration with sequential validation steps | **Chain of Responsibility** | [chain-of-responsibility](./chain-of-responsibility/README.md) | Already used in `ai-agent` module (validation → sanitization → LLM). Continue this style for new pipelines. |
| Multi-step object construction with many optional fields | **Builder** | [builder](./builder/README.md) | Use for complex query builders, report definitions, contract drafts with telescoping constructors. |

### Patterns to avoid at this layer
- **Singleton** as a code pattern — use NestJS DI scopes instead. Manual singletons fight the framework.
- **Prototype** — Sequelize models aren't cloneable cleanly. Use DTOs + `Object.assign`.

### Anchors
- God service to model new code against (or away from): `back/conexis/src/modules/contracts/services/contracts.service.ts` (~12.4k lines)
- DTO example: `back/conexis/src/modules/contracts/dto/contracts.dto.ts`
- Email helper sprawl: `back/conexis/src/modules/contracts/emails/contract.emails.ts`
- AI pipeline (good example of CoR-style): `back/conexis/src/modules/ai-agent/services/`

---

## 3. Frontend (Next.js 12)

### Sanctioned patterns

| Trigger | Pattern | Doc | Notes |
|---|---|---|---|
| Resource service with repeated error wrap + auth + cancellation per method | **Template Method** | [template-method](./template-method/README.md) | `ResourceService` base owns skeleton; subclasses override URL/payload only. Eliminates 40+ duplicated try/catches. |
| Need to add cross-cutting concerns (retry, telemetry, error transform) to specific resource methods | **Decorator** | [decorator](./decorator/README.md) | Compose `withErrorWrap(withRetry(method))`. Pick over TM when concerns are mix-and-match per call. |
| Multi-step forms (Buyer onboarding, contract creation, T&E entry) | **Composite** | [composite](./composite/README.md) | Tree of `FormStep` components sharing `validate()` / `submit()`. Recursive aggregation. |
| Multiple components calling `useTenantMetadata([flag])` for the same feature | **Facade** (feature hook) | [facade](./facade/README.md) | Wrap into a named hook, e.g. `useContractsListPermissions()`. Canonical example: `useShowClientNameAndFlowDown.tsx`. Respect [[feedback_no_hardcode_tenant_buyer]]. |
| Tenant/buyer/role-driven UI behavior selection | **Strategy** (flag-axis) | [strategy](./strategy/README.md) | UI behavior picked by `permissions.<flag>`. Concrete strategy = component variant or render function. |
| Pub/sub for app state | **Observer** | [observer](./observer/README.md) | Redux Toolkit already implements this. Validates current choice for client state. |
| Server data fetched + cached + revalidated | **Observer** via SWR | [observer](./observer/README.md) | New server-fetch features → SWR (already in deps). Existing Redux slices → leave; migrate only when touching them. UI/session state stays in Redux. |

### Patterns to avoid at this layer
- **Singleton** in React — use Context + Provider or atom (Jotai) instead.
- **Builder** for component props — TypeScript discriminated unions cover this cleaner.

### Anchors
- Hook composition canonical: `front/conexis/src/components/hooks/useShowClientNameAndFlowDown.tsx`
- Tenant hook: `front/conexis/src/components/hooks/useTenantMetadata.tsx`
- Role hook: `front/conexis/src/components/hooks/useTenantRoleMetadata.tsx`
- Role consumer example: `front/conexis/src/components/common/timeExpenseComponents/timeExpenseDetails/DetailsSections/ContractPricingSection.tsx:45-47, :79`
- Resource pattern: `front/conexis/src/infrastructure/services/*Resource.ts` + `*Services.ts`
- API client: `front/conexis/src/infrastructure/api/axiosClient.ts`

---

## 4. Database (PostgreSQL + Sequelize)

### Sanctioned patterns

| Trigger | Pattern | Doc | Notes |
|---|---|---|---|
| Service directly calling `Model.findAll/findOne/create` | **Adapter** (Repository) | [adapter](./adapter/README.md) | Wrap Sequelize models in `I<Domain>Repository`. Services consume the interface. Decouples from ORM. |
| Every query needs manual `where: { [tenant FK]: tenantId }` | **Proxy** (tenant-scoping) | [proxy](./proxy/README.md) | `TenantScopedRepositoryProxy` auto-injects tenant filter before delegating. Must read FK column per model — memory: [[feedback_verify_column_names]]. |
| Connection pool / Sequelize instance | **Singleton** | [singleton](./singleton/README.md) | NestJS-managed. Validates existing. No change. |
| Repository skeleton shared across domains (`findByTenant`, `byStatus`, `paginated`) | **Template Method** | [template-method](./template-method/README.md) | Abstract `BaseRepository<T>` with template methods; per-entity subclasses override only specifics. |

### Patterns to avoid at this layer
- **Bridge** (ORM abstraction for future swap) — premature today. Adapter alone is enough.
- **Prototype** — don't clone Sequelize model instances; use `toJSON()` or DTOs.
- Business logic inside `@BeforeCreate` / `@AfterFind` hooks — pull into services or repository layer.

### Anchors
- Tenant FK mix: `jobs.id_tenant` vs `contracts.tenant_id` — confirm per model.
- Models: `back/conexis/src/modules/*/models/*.model.ts`
- Migrations: `back/conexis/src/modules/database/migrations` (223 files)
- Seeders: `back/conexis/src/modules/database/seeders`
- Transactions: example `back/conexis/src/modules/payments/services/payments.service.ts:83`

---

## 5. Lambda (7 functions in `back/lambda/`)

### Sanctioned patterns

| Trigger | Pattern | Doc | Notes |
|---|---|---|---|
| New lambda handler — SQS parse, validate, process, callback | **Template Method** | [template-method](./template-method/README.md) | Abstract `SqsHandler` in shared lib. Subclass overrides `process()` only. Stops 7× copy-paste. |
| Cross-cutting lambda concerns (logger, idempotency, DLQ, retry) | **Chain of Responsibility** | [chain-of-responsibility](./chain-of-responsibility/README.md) | Middleware chain wraps handler core. Each middleware = one concern. |
| HTTP callback to NestJS API | **Adapter** | [adapter](./adapter/README.md) | One shared `BackendApiAdapter` (auth + retry + structured errors). Replaces 3× axios wrappers. |
| SQS message schema shared between producer (BE) and consumer (Lambda) | **Command** | [command](./command/README.md) | Command class with typed payload. Lives in shared lib so both sides compile against it. |
| Email template selection (if ever consolidated into lambda) | **Strategy** | [strategy](./strategy/README.md) | One strategy per template kind. Currently delegated to API — keep that until requirements change. |
| Idempotency dedupe store | **Proxy** | [proxy](./proxy/README.md) | Wraps handler with "already processed?" check. AWS Lambda Powertools + DynamoDB recommended (TTL + atomic conditional writes + no RDS pool pressure). |

### Patterns to avoid at this layer
- Per-lambda copy-paste utilities — always pull to shared lib (NPM workspace) once duplication hits 3 (memory: [[feedback_reuse_first_and_patterns]]).
- Per-lambda axios setup — use the shared Adapter.

### Anchors
- 7 lambdas: `back/lambda/{approve_contracts, approve_submission, approve_tande, convert_submission_to_contract, send-email-notification, inject-jobs, notify-not-approved-time-cards}`
- SQS message shape: `Records[].messageAttributes.{Body, Token, URL}.stringValue`
- Producer side: `back/conexis/src/common/services/simpleQueue.service.ts`, `back/conexis/src/aws/sqs/client.ts`

---

## Smell Index (reverse lookup)

| You see / feel | Reach for | Layer hint |
|---|---|---|
| Service file >2k lines doing many things | **Facade** (split) | Backend |
| `if (status === X) {…} else if (status === Y) {…}` repeated across methods | **State** | Backend |
| `if (buyer?.X)` / `if (tenant?.X)` chains | **Strategy** (flag-axis) | Backend / Frontend |
| Multiple resolvers/checks running in order, any can short-circuit | **Chain of Responsibility** | Architecture / Lambda |
| 3+ duplicated try/catch / boilerplate wrappers | **Template Method** or **Decorator** | Frontend / Lambda |
| Many call sites doing the same composite operation | **Facade** | Any |
| Object created with telescoping constructors / many optional args | **Builder** | Backend |
| Object cloning needed across types | **Prototype** | Avoid in Conexis; use DTOs |
| Async job dispatched and serialized | **Command** | Backend ↔ Lambda |
| Need to add observability/auth/retry to existing service | **Decorator** or **Proxy** | Any |
| Service tightly coupled to ORM, hard to test | **Adapter** (Repository) | Database |
| Tenant filter forgotten in queries → leak risk | **Proxy** (auto-scope) | Database |
| Template/algorithm body shared across domains with steps differing | **Template Method** | Any |
| Many entity types need same operation injected without modifying entities | **Visitor** | Backend (rarely; consider Strategy first) |
| Memory-heavy collections of similar objects | **Flyweight** | Backend (rarely; profile first) |
| Component composition: tree of UI parts with shared behavior | **Composite** | Frontend |
| Pub/sub between components | **Observer** | Frontend (Redux) |

---

## Patterns NOT used in Conexis (and why)

| Pattern | Status | Reason |
|---|---|---|
| **Abstract Factory** | Reserved | Useful only if multiple product families with variants emerge (e.g. multi-region UI kits). Not today. |
| **Bridge** | Deferred | Premature for tenant × role; defer until a 2nd permission resolver appears. |
| **Flyweight** | Edge case only | Conexis isn't memory-bound. Profile before reaching for it. |
| **Memento** | Use sparingly | Sequelize transactions cover most rollback needs. Apply only for true undo/redo UX. |
| **Mediator** | Not currently | Redux already acts as a mediator-ish hub on FE. BE doesn't need a custom mediator. |
| **Visitor** | Last resort | Prefer Strategy or Template Method. Visitor adds visitor-class churn whenever entity types change. |
| **Iterator** | Native | JavaScript iterators + Sequelize cursors cover this. No custom Iterator needed. |

---

## Pattern → Layer matrix (quick lookup)

| Pattern | Architecture | Backend | Frontend | Database | Lambda |
|---|:---:|:---:|:---:|:---:|:---:|
| Factory Method | | ✓ | | | |
| Abstract Factory | | | | | |
| Builder | | ✓ | | | |
| Prototype | | | | | |
| Singleton | ✓ (NestJS) | ✓ (DI) | | ✓ (pool) | |
| Adapter | | | | ✓ (repo) | ✓ (API) |
| Bridge | (defer) | | | (defer) | |
| Composite | | | ✓ | | |
| Decorator | | | ✓ | | |
| Facade | ✓ | ✓ | ✓ | | |
| Flyweight | | | | | |
| Proxy | | | | ✓ (tenant) | ✓ (idempotency) |
| Chain of Responsibility | ✓ (guards) | ✓ (AI pipeline) | | | ✓ (middleware) |
| Command | | ✓ | | | ✓ |
| Iterator | | | | | |
| Mediator | | | | | |
| Memento | | | | | |
| Observer | | | ✓ (Redux/SWR) | | |
| State | | ✓ (status FSM) | | | |
| Strategy | ✓ (tenant cfg) | ✓ (buyer flags) | ✓ (UI variant) | | ✓ (template) |
| Template Method | | ✓ (workflow) | ✓ (resource) | ✓ (repo base) | ✓ (handler) |
| Visitor | | | | | |

---

## When in doubt

1. Search the codebase for an existing pattern doing what you need (memory: [[feedback_reuse_first_and_patterns]]).
2. If found → reuse / extend.
3. If not found → match smell to this playbook → pick pattern → read its README.md.
4. If your case crosses module boundaries → stop and flag, don't extract drive-by (memory: [[feedback_scope_discipline]]).
5. If your case looks new → propose a pattern in your phase doc, cite this playbook, and ask the user before introducing.
