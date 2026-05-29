# Go — DDD Examples

DDD in Go uses structs + interfaces + unexported fields. No classes, no inheritance. The same tactical patterns apply: Entities, Value Objects, Aggregates, Domain Events, Repositories.

---

## Folder Structure (Bounded Context)

```
internal/
  user/                        # Bounded Context
    domain/
      user.go                  # Aggregate Root + Entity
      user_id.go               # Value Object
      email.go                 # Value Object
      events.go                # Domain Events
      repository.go            # Repository interface (port)
    application/
      register_user.go         # Use case
      register_user_command.go
    infrastructure/
      postgres_user_repository.go  # Repository implementation (adapter)
```

---

## Value Object

```go
// email.go

package domain

import (
    "errors"
    "strings"
)

type Email struct {
    value string
}

func NewEmail(raw string) (Email, error) {
    normalized := strings.ToLower(strings.TrimSpace(raw))
    if !strings.Contains(normalized, "@") {
        return Email{}, errors.New("invalid email address")
    }
    return Email{value: normalized}, nil
}

func (e Email) String() string   { return e.value }
func (e Email) Equals(o Email) bool { return e.value == o.value }
```

```go
// user_id.go

package domain

import "github.com/google/uuid"

type UserID struct {
    value string
}

func NewUserID() UserID {
    return UserID{value: uuid.New().String()}
}

func UserIDFromString(raw string) (UserID, error) {
    if _, err := uuid.Parse(raw); err != nil {
        return UserID{}, fmt.Errorf("invalid user ID: %w", err)
    }
    return UserID{value: raw}, nil
}

func (id UserID) String() string     { return id.value }
func (id UserID) Equals(o UserID) bool { return id.value == o.value }
```

---

## Aggregate Root

```go
// user.go

package domain

import "time"

// User is the Aggregate Root
// All access to the aggregate goes through User
type User struct {
    id        UserID
    email     Email
    name      string
    active    bool
    createdAt time.Time
    events    []DomainEvent
}

// Named constructor — enforces invariants at creation time
func NewUser(id UserID, email Email, name string) (*User, error) {
    if strings.TrimSpace(name) == "" {
        return nil, errors.New("name cannot be blank")
    }
    u := &User{
        id:        id,
        email:     email,
        name:      name,
        active:    true,
        createdAt: time.Now(),
    }
    u.record(NewUserRegistered(id, email))
    return u, nil
}

// Reconstitution from persistence — no domain event recorded
func ReconstitueUser(id UserID, email Email, name string, active bool, createdAt time.Time) *User {
    return &User{id: id, email: email, name: name, active: active, createdAt: createdAt}
}

// Behavior — validates and records events
func (u *User) ChangeEmail(newEmail Email) error {
    if u.email.Equals(newEmail) {
        return nil
    }
    oldEmail := u.email
    u.email = newEmail
    u.record(NewUserEmailChanged(u.id, oldEmail, newEmail))
    return nil
}

func (u *User) Deactivate() {
    if !u.active { return }
    u.active = false
    u.record(NewUserDeactivated(u.id))
}

// Getters — read-only access
func (u *User) ID() UserID        { return u.id }
func (u *User) Email() Email      { return u.email }
func (u *User) Name() string      { return u.name }
func (u *User) IsActive() bool    { return u.active }
func (u *User) CreatedAt() time.Time { return u.createdAt }

// Domain event collection
func (u *User) Events() []DomainEvent { return u.events }
func (u *User) ClearEvents()          { u.events = nil }

func (u *User) record(e DomainEvent) { u.events = append(u.events, e) }
```

---

## Domain Events

```go
// events.go

package domain

import "time"

type DomainEvent interface {
    EventName() string
    OccurredAt() time.Time
    AggregateID() string
}

// UserRegistered event
type UserRegistered struct {
    userID     UserID
    email      Email
    occurredAt time.Time
}

func NewUserRegistered(id UserID, email Email) UserRegistered {
    return UserRegistered{userID: id, email: email, occurredAt: time.Now()}
}

func (e UserRegistered) EventName() string     { return "user.registered" }
func (e UserRegistered) OccurredAt() time.Time { return e.occurredAt }
func (e UserRegistered) AggregateID() string   { return e.userID.String() }
func (e UserRegistered) UserID() UserID        { return e.userID }
func (e UserRegistered) Email() Email          { return e.email }

// UserEmailChanged event
type UserEmailChanged struct {
    userID     UserID
    oldEmail   Email
    newEmail   Email
    occurredAt time.Time
}

func NewUserEmailChanged(id UserID, old, new Email) UserEmailChanged {
    return UserEmailChanged{userID: id, oldEmail: old, newEmail: new, occurredAt: time.Now()}
}

func (e UserEmailChanged) EventName() string     { return "user.email_changed" }
func (e UserEmailChanged) OccurredAt() time.Time { return e.occurredAt }
func (e UserEmailChanged) AggregateID() string   { return e.userID.String() }
```

---

## Repository Interface (Port)

```go
// repository.go

package domain

import "context"

// UserRepository is defined in the domain — implemented in infrastructure
type UserRepository interface {
    Save(ctx context.Context, user *User) error
    FindByID(ctx context.Context, id UserID) (*User, error)
    FindByEmail(ctx context.Context, email Email) (*User, error)
    ExistsByEmail(ctx context.Context, email Email) (bool, error)
}
```

---

## Use Case (Application Service)

```go
// register_user.go

package application

import (
    "context"
    "myapp/internal/user/domain"
)

type RegisterUserCommand struct {
    Email string
    Name  string
}

type RegisterUserUseCase struct {
    users    domain.UserRepository
    eventBus EventBus
}

func NewRegisterUserUseCase(users domain.UserRepository, bus EventBus) *RegisterUserUseCase {
    return &RegisterUserUseCase{users: users, eventBus: bus}
}

func (uc *RegisterUserUseCase) Execute(ctx context.Context, cmd RegisterUserCommand) error {
    email, err := domain.NewEmail(cmd.Email)
    if err != nil { return err }

    exists, err := uc.users.ExistsByEmail(ctx, email)
    if err != nil { return err }
    if exists { return ErrEmailAlreadyTaken }

    id := domain.NewUserID()
    user, err := domain.NewUser(id, email, cmd.Name)
    if err != nil { return err }

    if err := uc.users.Save(ctx, user); err != nil { return err }

    return uc.eventBus.Publish(ctx, user.Events()...)
}

var ErrEmailAlreadyTaken = errors.New("email already taken")
```

---

## Repository Implementation (Adapter)

```go
// postgres_user_repository.go

package infrastructure

import (
    "context"
    "database/sql"
    "myapp/internal/user/domain"
)

type PostgresUserRepository struct {
    db *sql.DB
}

func NewPostgresUserRepository(db *sql.DB) *PostgresUserRepository {
    return &PostgresUserRepository{db: db}
}

func (r *PostgresUserRepository) Save(ctx context.Context, user *domain.User) error {
    _, err := r.db.ExecContext(ctx,
        `INSERT INTO users (id, email, name, active, created_at)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (id) DO UPDATE SET email = $2, name = $3, active = $4`,
        user.ID().String(),
        user.Email().String(),
        user.Name(),
        user.IsActive(),
        user.CreatedAt(),
    )
    return err
}

func (r *PostgresUserRepository) FindByID(ctx context.Context, id domain.UserID) (*domain.User, error) {
    row := r.db.QueryRowContext(ctx,
        `SELECT id, email, name, active, created_at FROM users WHERE id = $1`,
        id.String(),
    )
    return r.scanUser(row)
}

func (r *PostgresUserRepository) scanUser(row *sql.Row) (*domain.User, error) {
    var rawID, rawEmail, name string
    var active bool
    var createdAt time.Time

    if err := row.Scan(&rawID, &rawEmail, &name, &active, &createdAt); err != nil {
        if errors.Is(err, sql.ErrNoRows) { return nil, nil }
        return nil, err
    }

    id, _ := domain.UserIDFromString(rawID)
    email, _ := domain.NewEmail(rawEmail)
    return domain.ReconstitueUser(id, email, name, active, createdAt), nil
}
```

---

## Anti-Corruption Layer (ACL)

```go
// When consuming an external service, translate at the boundary

// External payment service response (we don't control this)
type StripeCustomer struct {
    StripeID    string `json:"id"`
    EmailAddr   string `json:"email"`
    PlanName    string `json:"plan"`
}

// Domain concept
type Subscriber struct {
    id    UserID
    email Email
    plan  SubscriptionPlan
}

// ACL translator — lives in infrastructure, translates into domain concepts
type StripeACL struct{}

func (a StripeACL) ToSubscriber(sc StripeCustomer) (Subscriber, error) {
    id, err := UserIDFromStripeID(sc.StripeID)
    if err != nil { return Subscriber{}, err }

    email, err := domain.NewEmail(sc.EmailAddr)
    if err != nil { return Subscriber{}, err }

    plan := planFromStripeName(sc.PlanName) // translates "stripe_premium" → domain.PremiumPlan

    return Subscriber{id: id, email: email, plan: plan}, nil
}
```

---

## CQRS — Query Side

```go
// Queries bypass the domain model and read directly from the database
// No aggregates, no value objects — just data transfer structs

type UserView struct {
    ID        string `json:"id"`
    Email     string `json:"email"`
    Name      string `json:"name"`
    Active    bool   `json:"active"`
    CreatedAt string `json:"createdAt"`
}

type UserQueryService struct {
    db *sql.DB
}

func (s *UserQueryService) FindActiveUsers(ctx context.Context) ([]UserView, error) {
    rows, err := s.db.QueryContext(ctx,
        `SELECT id, email, name, active, created_at FROM users WHERE active = true ORDER BY created_at DESC`,
    )
    if err != nil { return nil, err }
    defer rows.Close()

    var users []UserView
    for rows.Next() {
        var u UserView
        var createdAt time.Time
        if err := rows.Scan(&u.ID, &u.Email, &u.Name, &u.Active, &createdAt); err != nil {
            return nil, err
        }
        u.CreatedAt = createdAt.Format(time.RFC3339)
        users = append(users, u)
    }
    return users, rows.Err()
}
```

---

## Domain Service

```go
// When an operation doesn't naturally belong to any single aggregate

package domain

type TransferService struct{}

// Transferring money involves two accounts — neither owns the operation
func (s TransferService) Transfer(from, to *Account, amount Money) error {
    if err := from.Debit(amount); err != nil {
        return fmt.Errorf("debit failed: %w", err)
    }
    if err := to.Credit(amount); err != nil {
        // compensate
        from.Credit(amount) // best-effort rollback; use saga for reliability
        return fmt.Errorf("credit failed: %w", err)
    }
    return nil
}
```
