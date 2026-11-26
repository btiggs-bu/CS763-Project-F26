Prompt

I am working on a project for a graduate course. I will be prompting an AI coding agent to build a backend service. I have attached a spec file detailing the service. I need to break this down into steps to instruct the AI agent to build the core features of this service. Can you provide an overview of the steps I should provide for the AI agent, as well as a brief explanation of why it makes sense to provide them in this order?

Response

Based on the specification in [spec.md](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a&EntityRepresentationId=a05a36b0-e233-41c0-8250-6c0724f01829), I would structure the AI agent's work into dependency-driven phases rather than by endpoint type. This minimizes rework, allows testing at each stage, and ensures business rules are enforced consistently throughout the application. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

## Recommended Build Order

### Phase 1: Project Foundation

**Objective:** Establish the application skeleton and development environment.

**Tasks**

1. Create FastAPI application structure.
2. Configure PostgreSQL connection.
3. Configure SQLAlchemy ORM and database session management.
4. Configure Alembic migrations.
5. Create application settings/configuration management.
6. Configure Docker and Docker Compose.
7. Implement centralized logging.
8. Implement global exception handling.
9. Create standardized API response and error models.

**Why First?** Everything else depends on a working application framework, database connectivity, migrations, and error handling. Building features before these foundations often results in significant refactoring later.

---

### Phase 2: Database Schema and Migrations

**Objective:** Create the complete database structure from the ERD.

**Tasks**

1. Create core tables:
    - USER
    - ROLE
    - USER_ROLE
2. Create thread hierarchy tables:
    - THREADS
    - PROJECT
    - COURSE
    - LAB
    - THREADS_GROUP
    - USER_THREADS
3. Create content tables:
    - POST
    - COMMENT
4. Create metadata tables:
    - TAG
    - THREADS_TAG
    - POST_TAG
5. Add all:
    - Primary keys
    - Foreign keys
    - Unique constraints
    - Check constraints
    - Indexes

**Why Second?** The database schema is the foundation for all models, schemas, services, and endpoints. You want the data structure stable before implementing application logic. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

---

### Phase 3: Domain Models and Pydantic Schemas

**Objective:** Create the application's internal representations.

**Tasks**

1. Create SQLAlchemy models for all entities.
2. Create Pydantic request models.
3. Create Pydantic response models.
4. Create shared enum definitions:

RoleType

ThreadType

RestrictionLevel

PostType

ModerationStatus

5. Implement field validation according to constraints.

**Why Third?** The models form the contract between the API, service layer, and database. These should exist before business logic implementation.

---

### Phase 4: Repository/Data Access Layer

**Objective:** Create reusable database operations.

**Tasks**

1. Create BaseRepository pattern.
2. Implement repositories for:
    - Users
    - Roles
    - Threads
    - Posts
    - Comments
    - Tags
3. Implement pagination support.
4. Implement filtering support.
5. Implement search query support.

**Why Fourth?** Business services should not directly interact with SQLAlchemy queries. Building repositories first results in cleaner, more testable code.

---

### Phase 5: User and Role Management

**Objective:** Implement the identity foundation.

**Tasks**

1. User CRUD endpoints.
2. Role assignment logic.
3. User-role validation.
4. Duplicate prevention checks.
5. User-thread association management.

**Endpoints**

GET /users

GET /users/{id}

POST /users

PUT /users/{id}

DELETE /users/{id}

**Why Before Other Features?** Threads, posts, comments, permissions, and moderation all depend on users and their assigned roles. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

---

### Phase 6: Thread Management

**Objective:** Implement the primary discussion structure.

**Tasks**

1. Thread CRUD.
2. Create Project threads.
3. Create Course threads.
4. Create Lab threads.
5. Thread hierarchy validation:
    - Lab → Course only
    - Course → Project only
    - Project → No children
6. Restriction level handling.
7. Thread membership management.

**Endpoints**

GET /discussions/threads

GET /discussions/threads/{id}

POST /discussions/threads

PUT /discussions/threads/{id}

DELETE /discussions/threads/{id}

**Why Here?** Posts cannot exist without threads. The hierarchy rules are one of the core business requirements and should be established before content creation. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

---

### Phase 7: Tag Management

**Objective:** Implement content categorization.

**Tasks**

1. Tag CRUD service.
2. Thread-tag association management.
3. Post-tag association management.
4. Duplicate relationship prevention.

**Why Before Posts?** Posts and threads both rely on tags. Implementing tags first simplifies content creation endpoints.

---

### Phase 8: Post Management

**Objective:** Implement the primary content system.

**Tasks**

1. Post CRUD.
2. Announcement creation.
3. Discussion creation.
4. Restriction inheritance logic.
5. Post visibility logic.
6. Filtering functionality.
7. Full-text search functionality.

**Business Rules**

- Announcement posts require Faculty/Admin.
- Default moderation status = active.
- Default restriction level = inherited.
- Thread restriction enforcement.

**Endpoints**

GET /discussions/posts

GET /discussions/posts/{id}

POST /discussions/posts

PUT /discussions/posts/{id}

DELETE /discussions/posts/{id}

**Why After Threads?** Posts depend on both users and threads, and must enforce thread-level permissions. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

---

### Phase 9: Comment System

**Objective:** Implement nested discussions.

**Tasks**

1. Comment CRUD.
2. Direct post replies.
3. Nested comment replies.
4. Recursive parent validation.
5. Restriction inheritance from posts.
6. Comment search/filtering.

**Endpoints**

GET /posts/{post_id}/comments

GET /posts/{post_id}/comments/{comment_id}

POST /posts/{post_id}/comments

PUT /posts/{post_id}/comments/{comment_id}

DELETE /posts/{post_id}/comments/{comment_id}

**Why After Posts?** Comments depend entirely on existing posts and inherit access restrictions from them. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

---

### Phase 10: Authorization and Permission Engine

**Objective:** Centralize all access control logic.

**Tasks**

1. Role-based authorization.
2. Thread restriction enforcement.
3. Post restriction enforcement.
4. Membership validation.
5. Faculty/Admin privilege validation.
6. Author-only update enforcement.

**Rules to Enforce**

Open Thread:

  Anyone may participate

Restricted Thread:

  Assigned users

  Faculty

  Admin

Closed Thread:

  Admin only

**Why Here?** At this point all entities exist and permission rules can be implemented comprehensively rather than piecemeal.

---

### Phase 11: Moderation Features

**Objective:** Implement reporting and moderation workflows.

**Tasks**

1. Post reporting.
2. Comment reporting.
3. Moderator review functions.
4. Hidden content handling.
5. Faculty/Admin moderation checks.

**Endpoints**

PUT /posts/{id}/report

PUT /posts/{id}/moderation

PUT /comments/{id}/report

PUT /comments/{id}/moderation

**Why After Authorization?** Moderation relies heavily on role and permission systems.

---

### Phase 12: Timeline Feature

**Objective:** Implement project/course/lab feeds.

**Tasks**

1. Timeline service.
2. Thread hierarchy traversal.
3. Chronological ordering.
4. Scope filtering.
5. Pagination.

**Endpoint**

GET /discussions/scopes/{scope_type}/{id}/timeline

**Why Near the End?** This feature aggregates data from threads, posts, users, permissions, and hierarchy structures. It depends on nearly every prior system. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

---

### Phase 13: Testing

**Tasks**

1. Unit tests:
    - Services
    - Repositories
    - Validators
2. Integration tests:
    - Database operations
    - API endpoints
3. Permission tests.
4. Hierarchy validation tests.
5. Moderation tests.
6. Timeline tests.

**Why Here?** Testing is easier once major functionality exists, though the AI agent should continuously add tests as features are completed.

---

### Phase 14: Documentation and Finalization

**Tasks**

1. OpenAPI documentation refinement.
2. Endpoint examples.
3. Seed data scripts.
4. Docker deployment verification.
5. Migration verification.
6. README creation.

---

## If You Are Using an Autonomous Coding Agent

I would actually prompt it with **8 major milestones** rather than 14 smaller ones:

1. Foundation & Infrastructure
2. Database Schema & Migrations
3. Models & Validation Schemas
4. Users, Roles, and Memberships
5. Threads & Hierarchy Management
6. Posts, Comments, and Tags
7. Authorization & Moderation
8. Timeline, Testing, and Documentation

This ordering closely follows the dependency chain in the ERD and API design and minimizes the chance that the AI agent will repeatedly rewrite earlier work as new requirements emerge from the specification. [[onedrive.live.com]](https://onedrive.live.com?cid=43ce62b469518e19&id=43CE62B469518E19!s6e257d7b93b64b46a13e01070076e13a)

One additional recommendation: before coding begins, instruct the agent to create the project using a layered architecture (`routers → services → repositories → models`) rather than putting business logic directly in FastAPI routes. This will make the authorization, moderation, and hierarchy rules much easier to implement and test later.

Prompt

The main goal of this project is to create a more basic functional API and database. User authorization, privilege validation, and restriction enforcement are out of scope for this implementation. Please provide steps again with that in mind.

Response

If authorization and restriction enforcement are intentionally out of scope, then I would simplify the build order significantly. The goal becomes: **create a functioning FastAPI service that correctly stores, retrieves, updates, deletes, and relates data according to the ERD and API specification**, without implementing role-based access control or complex business permissions.

In that case, I'd recommend the AI agent build the system in the following order:

## Phase 1: Project Setup and Infrastructure

### Tasks

1. Create FastAPI application structure.
2. Configure PostgreSQL connection.
3. Configure SQLAlchemy ORM.
4. Configure Alembic migrations.
5. Create Docker and Docker Compose configuration.
6. Configure application settings.
7. Create global exception handling.
8. Create standard API response and error structures.

### Why First?

Every other feature depends on the application being able to start, connect to the database, and run migrations successfully.

---

## Phase 2: Database Schema Implementation

### Tasks

Create all database tables from the ERD:

#### Core Tables

- USER
- ROLE
- USER_ROLE

#### Thread Tables

- THREADS
- PROJECT
- COURSE
- LAB
- THREADS_GROUP
- USER_THREADS

#### Content Tables

- POST
- COMMENT

#### Tag Tables

- TAG
- THREADS_TAG
- POST_TAG

### Additional Tasks

Implement:

- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Indexes

### Why Second?

The database structure drives everything else. The API and models can't be reliably developed until the schema exists.

---

## Phase 3: Models and API Schemas

### Tasks

#### SQLAlchemy Models

Create ORM models for every entity.

#### Pydantic Schemas

Create:

- Create schemas
- Update schemas
- Response schemas

#### Enums

Create enums for:

RoleType

ThreadType

RestrictionLevel

PostType

ModerationStatus

#### Validation

Implement field constraints from the specification.

Examples:

username: 3-50 chars

title: 1-200 chars

content: 1-10000 chars

tag: 1-50 chars

### Why Third?

The API contracts are now defined before endpoint implementation begins.

---

## Phase 4: Repository / CRUD Layer

### Tasks

Create reusable database operations for:

- Users
- Roles
- Threads
- Projects
- Courses
- Labs
- Posts
- Comments
- Tags

Implement:

Create

Get by ID

Get all

Update

Delete

### Why Fourth?

Once CRUD functionality is centralized, endpoints become extremely simple.

---

## Phase 5: User and Role Endpoints

### Tasks

Implement:

GET /users

GET /users/{id}

POST /users

PUT /users/{id}

DELETE /users/{id}

Support filtering:

role_id

thread_id

Implement:

- User creation
- User updates
- Role assignment storage
- User-thread association storage

### Why First Feature?

Users are foundational data referenced throughout the rest of the schema.

---

## Phase 6: Thread Management

### Tasks

Implement:

GET /discussions/threads

GET /discussions/threads/{id}

POST /discussions/threads

PUT /discussions/threads/{id}

DELETE /discussions/threads/{id}

Support:

user_id

thread_type

restriction_level

tag_id

parent_thread_id

Implement hierarchy relationships:

Lab

 └─ Course

      └─ Project

Store:

- Thread tags
- Parent-child relationships
- User-thread relationships

### Why Here?

Threads are the parent objects for posts and timeline views.

---

## Phase 7: Tag Management

### Tasks

Implement internal services for:

- Creating tags automatically if needed
- Associating tags with threads
- Associating tags with posts

Enforce uniqueness constraints.

### Why Before Posts?

Posts and threads both use tags extensively.

---

## Phase 8: Post Endpoints

### Tasks

Implement:

GET /discussions/posts

GET /discussions/posts/{id}

POST /discussions/posts

PUT /discussions/posts/{id}

DELETE /discussions/posts/{id}

Support filters:

keyword

thread_id

user_id

post_type

tag_id

mod_status

Implement:

- Full-text search
- Tag associations
- Thread associations
- Announcement/discussion types
- Moderation status storage

### Why After Threads?

Posts cannot exist without threads.

---

## Phase 9: Comment Endpoints

### Tasks

Implement:

GET /discussions/posts/{post_id}/comments

GET /discussions/posts/{post_id}/comments/{comment_id}

POST /discussions/posts/{post_id}/comments

PUT /discussions/posts/{post_id}/comments/{comment_id}

DELETE /discussions/posts/{post_id}/comments/{comment_id}

Implement:

- Direct comments on posts
- Replies to comments
- Parent comment tracking
- Comment filtering
- TXT export option

### Why After Posts?

Comments depend entirely on posts.

---

## Phase 10: Moderation Status Endpoints

### Tasks

Implement:

PUT /posts/{id}/report

PUT /posts/{id}/moderation

PUT /comments/{id}/report

PUT /comments/{id}/moderation

For this project these endpoints simply:

- Update mod_status
- Return updated resource

No authorization checks required.

### Why Separate?

These endpoints perform a different business operation than normal updates and mirror the specification.

---

## Phase 11: Timeline Endpoint

### Tasks

Implement:

GET /discussions/scopes/{scope_type}/{id}/timeline

Functionality:

- Collect posts associated with a thread
- Return chronological ordering
- Support Project, Course, and Lab scopes
- Aggregate child-thread content where necessary

### Why Near the End?

This endpoint depends on threads, hierarchy relationships, and posts all functioning correctly.

---

## Phase 12: Testing and Seed Data

### Tasks

Create:

#### Unit Tests

- Validation
- CRUD operations
- Search functionality

#### Integration Tests

- Endpoint behavior
- Database persistence
- Timeline generation

#### Seed Data

- Roles
- Example users
- Labs
- Courses
- Projects
- Sample posts/comments

### Why Last?

Testing is easiest once all functionality exists.

---

# Condensed Agent Prompt Structure

If you're driving an autonomous coding agent, I'd actually use these **7 implementation milestones**:

1. **Project setup, Docker, PostgreSQL, SQLAlchemy, Alembic**
2. **Implement database schema from ERD**
3. **Create SQLAlchemy models and Pydantic schemas**
4. **Implement User, Role, and Thread CRUD endpoints**
5. **Implement Tag, Post, and Comment CRUD endpoints**
6. **Implement moderation and timeline endpoints**
7. **Add tests, seed data, and OpenAPI documentation**

This order follows the actual dependency chain of your data model while avoiding authorization work that your project explicitly excludes. It is also likely the most efficient sequence for an AI coding agent because each milestone produces a complete, testable piece of the system before moving to the next.

Prompt

Can you briefly explain what Alembic is needed for in this project?

Response

For your project, **Alembic is primarily used for database schema migrations**, meaning it manages changes to the PostgreSQL database structure over time.

### Why You Might Want Alembic

When you first create your database models, Alembic can generate and apply SQL scripts to create all of the tables from your ERD:

USER

ROLE

USER_ROLE

THREADS

PROJECT

COURSE

LAB

POST

COMMENT

TAG

...

Later, if you modify the schema, Alembic can generate migration scripts to update the existing database without manually rewriting SQL.

For example:

**Initial version**

class User(Base):

    username = Column(String(50))

**Later version**

class User(Base):

    username = Column(String(50))

    display_name = Column(String(100))

Alembic would generate a migration that adds the new column rather than requiring you to drop and recreate the table.

---

### Why It Is Useful for a Graduate Project

Even though your project is relatively straightforward, you'll likely make changes as you develop:

- Add fields
- Change field lengths
- Add indexes
- Add constraints
- Modify relationships

Without Alembic, each change requires manual SQL and can be error-prone. With Alembic:

alembic revision --autogenerate -m "add display_name"

alembic upgrade head

the database is updated automatically.

---

### Is Alembic Strictly Necessary?

**No.**

For a basic course project, you could instruct the AI agent to:

1. Create the SQLAlchemy models.
2. Use:

Base.metadata.create_all(bind=engine)

to create all tables when the application starts.

This is simpler and perfectly acceptable if:

- The database will be created once.
- You're not concerned with production-style schema management.
- You don't expect major schema revisions after initial development.

---

### My Recommendation

For your assignment, I would ask the AI agent:

> "Configure Alembic migrations, but keep them minimal. Use Alembic to create the initial database schema and support future schema changes. Focus on functionality over advanced migration workflows."

That gives you:

- Industry-standard tooling
- A more realistic FastAPI/PostgreSQL architecture
- A migration history you can discuss in project documentation

without adding much complexity to the implementation.

If your goal is the **simplest possible implementation that still satisfies the project requirements**, you could even omit Alembic entirely and have the agent use `Base.metadata.create_all()` to initialize the database. For a grading rubric focused on API functionality rather than DevOps practices, that would likely be sufficient.

Prompt

I am starting with the first milestone: Project setup, Docker, PostgreSQL, SQLAlchemy, Alembic

Response

For the **first milestone**, I would keep the AI agent focused on creating a stable foundation and explicitly avoid implementing any business entities or API endpoints yet.

### Milestone 1 Goal

> Create a runnable FastAPI application with Dockerized PostgreSQL, SQLAlchemy integration, Alembic migrations, configuration management, and a clean project structure that future milestones can build upon.

---

## Step 1: Create Project Structure

Have the agent create a layered architecture:

app/

├── api/

├── core/

├── db/

├── models/

├── schemas/

├── repositories/

├── services/

├── tests/

├── main.py

alembic/

alembic.ini

docker/

Dockerfile

docker-compose.yml

requirements.txt

.env

.env.example

### Why First?

The structure should exist before any implementation begins so future work is organized consistently.

---

## Step 2: Configure Dependencies

Install and configure:

FastAPI

Uvicorn

SQLAlchemy

psycopg2-binary

Alembic

Pydantic

python-dotenv

Generate a requirements file.

### Deliverable

Application can start locally:

uvicorn app.main:app --reload

---

## Step 3: Configure Environment Variables

Create:

.env

.env.example

Example:

POSTGRES_USER=postgres

POSTGRES_PASSWORD=postgres

POSTGRES_DB=rbpdb

DB_HOST=db

DB_PORT=5432

DATABASE_URL=postgresql://postgres:postgres@db:5432/rbpdb

### Why Now?

Everything else depends on database connection settings.

---

## Step 4: Configure PostgreSQL Container

Create:

docker-compose.yml

with services:

api

postgres

Requirements:

- PostgreSQL persists data using a Docker volume
- API waits for database availability
- Containers communicate through Docker networking

### Deliverable

docker compose up

starts both containers successfully.

---

## Step 5: Configure SQLAlchemy

Create:

app/db/database.py

Implement:

- Engine creation
- SessionLocal factory
- Declarative Base

Example responsibilities:

engine

SessionLocal

Base

get_db()

### Deliverable

Application can establish a database session successfully.

---

## Step 6: Configure Settings Management

Create:

app/core/config.py

Load values from:

DATABASE_URL

using Pydantic settings.

### Why?

Avoid hardcoding connection strings and make the application portable.

---

## Step 7: Configure Alembic

Initialize Alembic:

alembic init alembic

Configure:

alembic.ini

alembic/env.py

to use the SQLAlchemy Base metadata.

### Deliverable

Agent can generate migrations:

alembic revision --autogenerate

and apply them:

alembic upgrade head

At this milestone there may be few or no tables yet. The important thing is verifying Alembic works.

---

## Step 8: Create Health Check Endpoint

Create a minimal endpoint:

GET /health

Response:

{

  "status": "healthy"

}

### Why?

Provides an easy way to verify the application is running.

---

## Step 9: Implement Database Health Check

Add database connectivity verification.

Example:

GET /health/db

Expected behavior:

- Open a database session
- Execute simple query
- Return success/failure

### Why?

Verifies FastAPI and PostgreSQL are communicating correctly.

---

## Step 10: Configure Error Handling

Create common exception handlers for:

Validation errors

Database errors

Unexpected exceptions

Use the error format defined in your specification.

### Why?

Prevents refactoring later when endpoints are added.

---

## Step 11: Verify Docker Workflow

The agent should confirm the following works:

docker compose up --build

alembic upgrade head

[http://localhost:8000/docs](http://localhost:8000/docs)

GET /health

GET /health/db

---

## Expected Deliverables at the End of Milestone 1

The application should have:

✅ FastAPI running

✅ PostgreSQL running in Docker

✅ SQLAlchemy configured

✅ Alembic configured

✅ Environment-based configuration

✅ Docker Compose working

✅ Health endpoints

✅ Standard error handling

✅ Project structure ready for expansion

❌ No entities

❌ No models

❌ No API business endpoints

❌ No CRUD operations

---

### Suggested Prompt for the AI Agent

This prompt should give the agent a very well-defined scope while preventing it from prematurely implementing data models or business logic.

Prompt

I am starting with the first milestone: Project setup, Docker, PostgreSQL, SQLAlchemy, Alembic

Please provide a series of prompts I can give to the AI coding agent to complete this milestone

Response

This is a great use case for an AI coding agent. Rather than giving it one huge prompt, you'll get much better results by breaking Milestone 1 into a series of focused prompts where each builds on the previous deliverable and can be validated before moving on.

---

# Prompt 1: Create the Project Skeleton

---

# Prompt 2: Configure Dependencies

---

# Prompt 3: Environment Configuration

---

# Prompt 4: Docker and PostgreSQL Setup

---

# Prompt 5: Configure SQLAlchemy

---

# Prompt 6: Configure Alembic

---

# Prompt 7: Create Initial Database Verification Migration

---

# Prompt 8: Create FastAPI Application Entry Point

---

# Prompt 9: Add Health Endpoints

---

# Prompt 10: Global Error Handling

---

# Prompt 11: Milestone Validation

### Why this sequence works

Each prompt introduces **one major concern at a time**:

1. Structure
2. Dependencies
3. Configuration
4. Containers
5. Database connectivity
6. Migrations
7. Migration validation
8. Application startup
9. Health monitoring
10. Error handling
11. Verification

This minimizes the chances of the AI agent generating a large amount of code that later needs to be rewritten, and it gives you a working, testable foundation before you begin Milestone 2 (database schema implementation).

Prompt

I am copying these responses into a Markdown document. Please repeat the previous response, but with all draft snippets inside a 4-backtick code block so I can copy the triple backticks directly.

Response

Absolutely. Below is the same content, but each prompt is wrapped in a **4-backtick code block** so you can copy it directly into your Markdown document while preserving the inner triple-colon writing-block syntax and formatting.

---

# Prompt 1: Create the Project Skeleton

Create the initial project structure for a FastAPI backend service named Research Blog & Project Discussion Board (RBPDB).

Technology stack:

- Python

- FastAPI

- PostgreSQL

- SQLAlchemy

- Alembic

- Docker

Implement only the project structure. Do not create business entities, API endpoints (except placeholders), or database models.

Create a clean layered architecture using the following directories:

app/

├── api/

├── core/

├── db/

├── models/

├── schemas/

├── repositories/

├── services/

├── tests/

├── main.py

alembic/

docker/

Also create:

- requirements.txt

- .env.example

- .gitignore

- README.md

- docker-compose.yml

- Dockerfile

Explain the purpose of every directory and file created.

---

# Prompt 2: Configure Dependencies

Using the project structure already created, configure dependencies for the service.

Add and configure:

- FastAPI

- Uvicorn

- SQLAlchemy

- psycopg2-binary

- Alembic

- Pydantic

- python-dotenv

Generate:

- requirements.txt

Update README.md with installation instructions.

Do not implement business entities or database models yet.

Provide all package versions and explain why each dependency is required.

---

# Prompt 3: Environment Configuration

Create environment variable management for the FastAPI application.

Requirements:

Create:

- .env.example

- app/core/config.py

Include configuration variables for:

- POSTGRES_USER

- POSTGRES_PASSWORD

- POSTGRES_DB

- DB_HOST

- DB_PORT

- DATABASE_URL

Use Pydantic settings to load configuration from environment variables.

Provide an explanation of how configuration values are loaded and accessed throughout the application.

---

# Prompt 4: Docker and PostgreSQL Setup

Configure Docker and Docker Compose for the project.

Requirements:

Create:

- Dockerfile

- docker-compose.yml

Docker Compose should include:

1. FastAPI service

2. PostgreSQL service

Requirements:

- PostgreSQL data persists using Docker volumes

- API and database communicate through Docker networking

- Environment variables are loaded from .env

- Containers restart automatically on failure

Provide commands to:

- Build containers

- Start containers

- Stop containers

- View logs

Do not implement application features at this stage.

---

# Prompt 5: Configure SQLAlchemy

Configure SQLAlchemy for the FastAPI project.

Create:

app/db/database.py

Requirements:

Implement:

- SQLAlchemy engine creation

- Base declarative class

- SessionLocal

- Database dependency function (get_db)

The implementation should support PostgreSQL and future database models.

Do not create any business models yet.

Explain how database sessions will be used by future API endpoints.

---

# Prompt 6: Configure Alembic

Configure Alembic migrations for the FastAPI application.

Requirements:

1. Initialize Alembic.

2. Configure alembic.ini.

3. Configure alembic/env.py.

4. Connect Alembic to the SQLAlchemy Base metadata.

5. Configure migrations using the DATABASE_URL environment variable.

Provide commands for:

- Creating migration files

- Generating migration files automatically

- Applying migrations

- Rolling back migrations

The project currently has no business entities or tables. Focus only on establishing a working migration framework.

---

# Prompt 7: Create Initial Database Verification Migration

Using the configured Alembic environment, create an initial migration that verifies the migration process is functioning correctly.

Requirements:

- Create a simple versioned migration.

- Apply the migration successfully.

- Verify migration history tracking works.

- Demonstrate the correct Alembic workflow that will be used later when database models are added.

Do not create application entities yet.

Explain how future migrations will be generated from SQLAlchemy models.

---

# Prompt 8: Create FastAPI Application Entry Point

Create the FastAPI application entry point.

Requirements:

Update:

- app/main.py

Implement:

- FastAPI application initialization

- API title

- Version information

- Basic application startup configuration

Do not add business routes.

Provide the command to run the application both:

1. Locally

2. Through Docker

---

# Prompt 9: Add Health Endpoints

Create health-check endpoints for the FastAPI application.

Requirements:

Implement:

GET /health

Response:

{

  "status": "healthy"

}

Implement:

GET /health/db

Requirements:

- Open a database session

- Execute a simple database query

- Return success or failure

Provide complete router implementation and explain how these endpoints verify application health.

---

# Prompt 10: Global Error Handling

Implement centralized exception handling for the FastAPI application.

Requirements:

Create handlers for:

- Request validation errors

- SQLAlchemy/database errors

- Unexpected server errors

Use a consistent error response format:

{

  "error": {

    "code": "ERROR_CODE",

    "message": "Human readable message"

  },

  "timestamp": "...",

  "request_id": "..."

}

Integrate exception handling into the FastAPI application startup process.

Provide examples of responses for each error type.

---

# Prompt 11: Milestone Validation

Review the entire project and verify Milestone 1 is complete.

Confirm:

- FastAPI starts successfully

- PostgreSQL starts successfully

- Docker Compose works

- Environment variables are loaded correctly

- SQLAlchemy connects to PostgreSQL

- Alembic is configured correctly

- Migrations can be generated and applied

- GET /health works

- GET /health/db works

- Swagger UI is accessible

- No business entities or API functionality have been implemented yet

Provide a checklist showing what has been completed and identify any missing items.

---

# Why this sequence works

1. Project structure
2. Dependencies
3. Configuration management
4. Docker infrastructure
5. Database connectivity
6. Alembic setup
7. Migration validation
8. Application startup
9. Health checks
10. Error handling
11. Final verification

Each prompt has a narrow scope and produces a verifiable deliverable before the next layer is added. This approach typically produces much cleaner results from autonomous coding agents than a single large "build the entire milestone" prompt.

Prompt

The next milestone is to implement the database schema from the ERD. How should I prompt the AI agent to do so and why?

Response

For the **Database Schema** milestone, I would again avoid giving the AI agent a single large prompt. Database design is foundational, and mistakes made here can cascade into every future milestone. Instead, have the agent progress through a series of prompts that move from understanding the ERD to implementing, validating, and testing the schema.

The rationale is simple:

1. **Understand the ERD first** before generating code.
2. **Design models second** before generating migrations.
3. **Review relationships and constraints** before creating tables.
4. **Generate migrations only after the schema is validated.**
5. **Verify the resulting database structure** before building APIs.

This significantly reduces the chance that the agent incorrectly interprets the ERD and forces major rewrites later.

---

# Prompt 1: Analyze the ERD and Create a Schema Plan

Review the provided ERD and project specification.

Do not generate implementation code yet.

Produce a database schema implementation plan that includes:

For each table:

- Table name

- Purpose

- Primary key

- Foreign keys

- Columns

- Data types

- Nullability

- Unique constraints

For each relationship:

- Relationship type

  - One-to-one

  - One-to-many

  - Many-to-many

- Parent table

- Child table

- Required foreign keys

Identify:

- Join tables

- Lookup/reference tables

- Enumerated values that should become Python enums

- Recommended indexes

Highlight any assumptions or ambiguities in the ERD before implementation begins.

No SQLAlchemy models or migrations should be generated yet.

---

# Prompt 2: Create SQLAlchemy Model Design

Using the approved database schema plan, design the SQLAlchemy ORM models for all entities.

Do not generate migration files yet.

For each model provide:

- Class name

- Table name

- Columns

- Data types

- Constraints

- Relationships

Implement models for:

- USER

- ROLE

- USER_ROLE

- THREADS

- PROJECT

- COURSE

- LAB

- THREADS_GROUP

- USER_THREADS

- POST

- COMMENT

- TAG

- THREADS_TAG

- POST_TAG

Use SQLAlchemy 2.x style.

Provide a complete review of relationships before generating implementation code.

---

# Prompt 3: Create Python Enums

Identify all fields in the ERD and specification that should be represented as Python enums.

Create enum definitions for all applicable values.

Examples may include:

- RoleType

- ThreadType

- RestrictionLevel

- PostType

- ModerationStatus

For each enum:

- Explain why an enum is appropriate.

- Provide values.

- Identify which database columns will use the enum.

Follow SQLAlchemy and PostgreSQL best practices.

---

# Prompt 4: Implement SQLAlchemy Models

Implement the SQLAlchemy models based on the approved schema design.

Requirements:

- Use SQLAlchemy 2.x declarative mappings.

- Place models in the app/models directory.

- Include primary keys.

- Include foreign keys.

- Include relationship definitions.

- Use enums where appropriate.

- Add indexes where beneficial.

- Add uniqueness constraints defined in the ERD.

Do not create Alembic migration files yet.

Explain the purpose of each relationship and constraint implemented.

---

# Prompt 5: Review Schema Consistency

Perform a complete schema review of all SQLAlchemy models.

Validate:

- All ERD entities are represented.

- All relationships are represented.

- Foreign keys are correct.

- Cascade behavior is appropriate.

- Naming conventions are consistent.

- Constraints match the project specification.

Provide a table showing:

- Entity

- Implemented

- Relationships Verified

- Constraints Verified

Identify any discrepancies before migrations are created.

---

# Prompt 6: Configure Alembic Metadata Detection

Update the Alembic configuration so all SQLAlchemy models are discoverable.

Requirements:

- Import all model metadata correctly.

- Verify Alembic autogenerate can detect schema changes.

- Verify target_metadata is configured properly.

Demonstrate the configuration without generating migrations yet.

Explain how Alembic discovers model changes from SQLAlchemy metadata.

---

# Prompt 7: Generate Initial Schema Migration

Generate the initial Alembic migration from the SQLAlchemy models.

Requirements:

- Use Alembic autogenerate.

- Produce a complete migration script.

- Create all tables in dependency order.

- Create indexes.

- Create foreign key constraints.

- Create uniqueness constraints.

Review the generated migration and explain each section before applying it.

---

# Prompt 8: Apply Migration and Validate Database Structure

Apply the initial migration to PostgreSQL.

After migration:

Verify:

- All tables were created.

- Primary keys exist.

- Foreign keys exist.

- Indexes exist.

- Constraints exist.

Provide a schema validation report showing:

- Table names

- Column counts

- Primary keys

- Foreign keys

- Indexes

Confirm the database structure matches the ERD exactly.

---

# Prompt 9: Create Seed Data Framework

Create a seed-data framework that can populate the database with test data.

Implement seed scripts for:

- Roles

- Users

- Labs

- Courses

- Projects

- Tags

The goal is to support future API testing.

Do not create large datasets.

Provide instructions for running and resetting seed data.

---

# Prompt 10: Milestone Validation

Review the database implementation and confirm Milestone 2 is complete.

Validate:

- All ERD entities exist.

- SQLAlchemy models compile successfully.

- All relationships function correctly.

- Alembic detects schema changes.

- Initial migration executes successfully.

- PostgreSQL contains every required table.

- Constraints match the ERD.

- Indexes are implemented where appropriate.

- Seed data framework works.

Provide a checklist of completed items and identify any remaining concerns before API development begins.

---

# Why this sequence works

The progression follows the dependency chain of database development:

1. **Understand the ERD**
2. **Design the schema**
3. **Define enums and constraints**
4. **Implement models**
5. **Review accuracy**
6. **Connect Alembic**
7. **Generate migrations**
8. **Create the database**
9. **Seed test data**
10. **Validate completion**

A common mistake with AI coding agents is asking them to "implement the database" immediately. They often jump straight into SQLAlchemy code and migrations before carefully analyzing the ERD. Having the agent explicitly produce a schema plan and relationship review first gives you a chance to catch errors while changes are still cheap, before those mistakes become models, migrations, repositories, and API endpoints.

Prompt

I now need to prompt the AI agent to create Pydantic schemas. I would like to do this in fewer prompts without omitting important instructions. Please generate up to 3 prompts for the AI agent to do so and explain why they work.

Response

For **Pydantic schemas**, you can safely compress the work into **2-3 prompts** because schema development is much more straightforward than database design. The key is to separate:

1. **Schema design and validation decisions**
2. **Schema implementation**
3. **Verification and cleanup**

This gives the agent enough room to think through the API contracts while avoiding excessive prompt fragmentation.

---

# Prompt 1: Design All Pydantic Schemas

Review the project specification, API endpoints, ERD, SQLAlchemy models, and field requirements.

Design all Pydantic schemas needed for the API.

For every entity, identify the schemas required for:

- Create operations

- Update operations

- Response operations

- List responses (if applicable)

Include schemas for:

- User

- Role

- UserRole

- Thread

- Project

- Course

- Lab

- ThreadGroup

- UserThread

- Post

- Comment

- Tag

For each schema:

- List included fields

- Required vs optional fields

- Validation constraints

- Relationship fields

- Nested object requirements

Follow these design principles:

- Create schemas should only contain fields that can be supplied by clients.

- Update schemas should support partial updates.

- Response schemas should include generated identifiers and related metadata.

- Do not expose internal database implementation details.

Provide a schema design review before implementing code.

---

# Prompt 2: Implement All Pydantic Schemas

Implement the approved Pydantic schemas.

Requirements:

Create schema modules within app/schemas.

For every major entity, implement:

- Base schema

- Create schema

- Update schema

- Response schema

Use Pydantic v2 conventions and best practices.

Implement field validation for all constraints defined in the project specification, including:

Examples:

- username length constraints

- title length constraints

- content length constraints

- tag name constraints

- email validation (if applicable)

Use enums where appropriate.

Implement proper schema inheritance to minimize duplication.

Add model_config settings required for ORM compatibility with SQLAlchemy models.

Do not create API endpoints yet.

Do not implement business logic.

Provide explanations for all inheritance relationships between schemas.

---

# Prompt 3: Validate Schema Completeness and API Alignment

Review all implemented Pydantic schemas and verify they fully support the API specification.

Validate that:

- Every endpoint request body has a corresponding schema.

- Every endpoint response has a corresponding schema.

- Required fields match the database design.

- Validation rules match the specification.

- Schema inheritance is appropriate.

- Enum fields are implemented consistently.

- ORM serialization works correctly.

Generate a coverage matrix showing:

- Endpoint

- Request Schema

- Response Schema

- Validation Complete (Yes/No)

Identify any missing schemas, duplicated logic, or opportunities for simplification before API endpoint implementation begins.

---

# Why These 3 Prompts Work

### Prompt 1: Forces the Agent to Think First

Many AI coding agents immediately start generating classes and end up with:

- Missing update schemas
- Inconsistent response models
- Duplicated fields
- Poor nesting decisions

This prompt creates an API contract before code is written.

---

### Prompt 2: Generates the Actual Code

At this point the agent has already decided:

- Which schemas exist
- How inheritance works
- Which fields are optional
- Which validators are required

The resulting code is usually much cleaner.

---

### Prompt 3: Prevents Endpoint Problems Later

This is the most commonly skipped step.

By checking schemas against endpoints before CRUD implementation, the agent can catch issues like:

- Missing response models
- Missing pagination models
- Missing nested schemas
- Incorrect optional/required fields

before you begin building repositories and routes.

---

For your project specifically, I would stop at these **3 prompts**. That's enough structure to produce high-quality Pydantic schemas while keeping the workflow efficient and avoiding the over-fragmentation that was useful for the database-schema milestone but isn't necessary here.

Prompt

Please generate one prompt to Implement User, Role, and Thread CRUD endpoints and one prompt to validate them.

Response

Since you've already completed:

- Project setup
- Docker/PostgreSQL
- SQLAlchemy
- Alembic
- Database schema/models
- Pydantic schemas

the next milestone should focus on implementing the **CRUD API layer**, not redesigning models or database structures. A single implementation prompt and a single validation prompt are sufficient.

---

## Prompt 1: Implement User, Role, and Thread CRUD Endpoints

Implement the User, Role, and Thread API functionality using the existing SQLAlchemy models, Pydantic schemas, and database configuration.

Requirements:

Architecture:

- Follow the existing layered architecture:

  - routers/api

  - services

  - repositories

  - models

  - schemas

- Keep business logic out of route handlers.

- Route handlers should delegate work to service classes.

- Services should use repositories for database access.

Implement CRUD functionality for:

Users

-----

GET    /users

GET    /users/{id}

POST   /users

PUT    /users/{id}

DELETE /users/{id}

Roles

-----

GET    /roles

GET    /roles/{id}

POST   /roles

PUT    /roles/{id}

DELETE /roles/{id}

Threads

-------

GET    /threads

GET    /threads/{id}

POST   /threads

PUT    /threads/{id}

DELETE /threads/{id}

Requirements:

User Endpoints

- Support create, retrieve, update, delete, and list operations.

- Return appropriate HTTP status codes.

- Validate request bodies using Pydantic schemas.

- Return response schemas consistently.

- Prevent creation of duplicate unique values where applicable.

Role Endpoints

- Implement complete CRUD operations.

- Validate enum values and role names.

- Return appropriate error responses.

Thread Endpoints

- Implement complete CRUD operations.

- Support parent-child thread relationships.

- Support thread type values defined in the specification.

- Support associations already defined in the database schema.

- Validate referenced entity IDs before persistence.

General Requirements

Repository Layer

- Create repositories for User, Role, and Thread entities.

- Reuse common CRUD functionality where practical.

Service Layer

- Implement business services for User, Role, and Thread operations.

- Handle validation and integrity checks within services.

API Layer

- Register routers with FastAPI.

- Group endpoints logically.

- Add endpoint summaries and descriptions for Swagger/OpenAPI.

Error Handling

- Use the existing exception framework.

- Return meaningful errors for:

  - entity not found

  - validation failures

  - duplicate records

  - foreign key violations

Deliverables

Provide:

- All new files created

- All modified files

- Complete implementation code

- OpenAPI endpoint summary

- Example requests and responses

---

## Prompt 2: Validate User, Role, and Thread CRUD Endpoints

Perform a complete validation review of the implemented User, Role, and Thread CRUD functionality.

Review the implementation against:

- Project specification

- ERD

- SQLAlchemy models

- Pydantic schemas

- Existing architecture

Validate the following:

Endpoint Coverage

-----------------

Verify all required endpoints exist:

Users

- GET /users

- GET /users/{id}

- POST /users

- PUT /users/{id}

- DELETE /users/{id}

Roles

- GET /roles

- GET /roles/{id}

- POST /roles

- PUT /roles/{id}

- DELETE /roles/{id}

Threads

- GET /threads

- GET /threads/{id}

- POST /threads

- PUT /threads/{id}

- DELETE /threads/{id}

Architecture Review

-------------------

Confirm:

- Routes contain minimal logic

- Services handle business operations

- Repositories handle database access

- Dependency injection is implemented properly

Schema Validation

-----------------

Confirm:

- Request schemas are correct

- Response schemas are correct

- Update schemas support partial updates

- ORM serialization functions correctly

Database Validation

-------------------

Confirm:

- Foreign keys are respected

- Relationships function correctly

- Cascade behavior is appropriate

- Unique constraints are enforced

API Behavior Validation

-----------------------

Verify:

- Correct HTTP status codes

- Consistent error responses

- OpenAPI documentation generation

- Resource creation and update behavior

- Resource deletion behavior

Testing Review

--------------

Generate and/or verify:

- Unit tests for services

- Repository tests

- API integration tests

Create a validation matrix showing:

| Area | Status | Notes |

|--------|--------|--------|

| User CRUD | Pass/Fail | |

| Role CRUD | Pass/Fail | |

| Thread CRUD | Pass/Fail | |

| Repositories | Pass/Fail | |

| Services | Pass/Fail | |

| Schemas | Pass/Fail | |

| OpenAPI Docs | Pass/Fail | |

| Integration Tests | Pass/Fail | |

Identify all defects, inconsistencies, missing functionality, or opportunities for simplification before proceeding to the next milestone.

---

### Why these prompts work

**Prompt 1** is implementation-focused and gives the agent enough architectural guidance to avoid common mistakes such as:

- Putting database queries directly in routes
- Mixing business logic into controllers
- Returning SQLAlchemy models directly
- Skipping validation

**Prompt 2** forces the agent to act as a reviewer rather than a developer. AI coding agents frequently produce code that "works" but does not fully align with the specification. This validation prompt verifies:

- endpoint completeness,
- architecture compliance,
- schema correctness,
- database integrity,
- and test coverage

before you move on to Posts, Comments, and Tags. This is typically the point where defects become much harder to fix if left undiscovered.

Prompt

Please generate one prompt to Implement Post and Comment CRUD endpoints and one prompt to validate them.

Response

## Prompt 1: Implement Post and Comment CRUD Endpoints

Implement the Post and Comment API functionality using the existing SQLAlchemy models

---

## Prompt 2: Validate Post and Comment CRUD Endpoints

Perform a complete validation review of the implemented Post and Comment functionality.

Review the implementation against:

- Project specification

- ERD

- SQLAlchemy models

- Pydantic schemas

- Existing architecture

Endpoint Coverage

-----------------

Verify all required endpoints exist:

Posts

- GET /posts

- GET /posts/{id}

- POST /posts

- PUT /posts/{id}

- DELETE /posts/{id}

Comments

- GET /posts/{post_id}/comments

- GET /posts/{post_id}/comments/{comment_id}

- POST /posts/{post_id}/comments

- PUT /posts/{post_id}/comments/{comment_id}

- DELETE /posts/{post_id}/comments/{comment_id}

Architecture Review

-------------------

Confirm:

- Routes contain minimal business logic

- Services encapsulate business functionality

- Repositories encapsulate data access

- Dependency injection is used consistently

- Existing architectural patterns are followed

Schema Validation

-----------------

Verify:

- All request schemas are correct

- All response schemas are correct

- Partial updates function correctly

- ORM serialization works correctly

- Enum fields serialize correctly

Relationship Validation

-----------------------

Verify:

Posts correctly reference:

- Users

- Threads

- Tags

Comments correctly reference:

- Posts

- Users

- Parent comments

Nested comment relationships function correctly.

Database Validation

-------------------

Verify:

- Foreign key constraints work correctly

- Deletes behave as intended

- Database integrity is maintained

- Required relationships are enforced

Filtering and Query Validation

------------------------------

Verify all filtering/search functionality defined in the specification works correctly.

Examples may include:

- Filter by thread

- Filter by author

- Filter by tag

- Filter by post type

- Filter by moderation status

- Keyword search

Adjust validation criteria according to the implemented API specification.

API Behavior Validation

-----------------------

Confirm:

- Correct HTTP status codes

- Consistent error responses

- Proper OpenAPI documentation

- Consistent request/response formats

Testing Review

--------------

Create and/or verify:

Unit Tests

- Post service tests

- Comment service tests

- Repository tests

Integration Tests

- Post CRUD operations

- Comment CRUD operations

- Nested comments

- Relationship validation

- Filtering and search functionality

Generate a validation matrix:

| Area | Status | Notes |

|--------|--------|--------|

| Post CRUD | Pass/Fail | |

| Comment CRUD | Pass/Fail | |

| Post Relationships | Pass/Fail | |

| Comment Relationships | Pass/Fail | |

| Repositories | Pass/Fail | |

| Services | Pass/Fail | |

| Schemas | Pass/Fail | |

| OpenAPI Docs | Pass/Fail | |

| Unit Tests | Pass/Fail | |

| Integration Tests | Pass/Fail | |

Identify:

- Missing functionality

- Specification mismatches

- Validation gaps

- Redundant code

- Opportunities for simplification

Provide recommended fixes before proceeding to the next milestone.

### Why these prompts work

**The implementation prompt** assumes the foundation is already complete and focuses exclusively on the Post and Comment domain. It explicitly scopes the work to CRUD operations, relationship validation, nested comments, and OpenAPI documentation while preventing the agent from drifting into authorization or permission logic that is out of scope for your project.

**The validation prompt** treats the implementation as a completed deliverable and forces the agent to verify endpoint coverage, schema correctness, relationship integrity, database behavior, and test coverage. This catches issues with nested comments, foreign keys, and filtering before you move on to the final milestone (tags, moderation endpoints, timeline endpoint, testing, and documentation).

Prompt

I've finished the prompts for API endpoints. Please generate a maximum of 2 prompts for the final milestone of this implementation, keeping in mind that some tests and seed data have already been created: Add needed tests, seed data, and OpenAPI documentation

Response

Since you've already implemented the API endpoints and some tests/seed data exist, the final milestone should focus on **completing coverage, improving documentation, and preparing the project for demonstration and grading** rather than generating entirely new functionality.

I would use **one implementation prompt** and **one validation/review prompt**.

---

# Prompt 1: Complete Testing, Seed Data, and OpenAPI Documentation

Complete the final implementation work for the Research Blog & Project Discussion Board (RBPDB) backend project.

The following components already exist:

- FastAPI application

- PostgreSQL integration

- SQLAlchemy models

- Alembic migrations

- Pydantic schemas

- User, Role, Thread, Post, and Comment CRUD endpoints

- Existing tests

- Existing seed data

Your task is to identify gaps and complete the remaining work related to testing, seed data, and API documentation.

Testing

-------

Review all existing tests and add any missing tests needed to achieve comprehensive coverage of implemented functionality.

Cover at minimum:

Users

- Create

- Retrieve

- Update

- Delete

- List

Roles

- Create

- Retrieve

- Update

- Delete

- List

Threads

- Create

- Retrieve

- Update

- Delete

- Parent-child relationship validation

Posts

- Create

- Retrieve

- Update

- Delete

- Thread associations

Comments

- Create

- Retrieve

- Update

- Delete

- Nested comment relationships

Include:

- Unit tests

- API integration tests

- Validation error tests

- Not-found scenarios

- Foreign key validation scenarios

Seed Data

---------

Review the existing seed data and expand it as needed to adequately demonstrate the application.

Create realistic sample records for:

- Roles

- Users

- Labs

- Courses

- Projects

- Threads

- Tags

- Posts

- Comments

Ensure the seed data demonstrates:

- Parent-child thread relationships

- Multiple users

- Multiple posts

- Nested comments

Provide a repeatable process for:

- Seeding the database

- Resetting seed data

OpenAPI Documentation

---------------------

Review and improve the generated OpenAPI documentation.

For every endpoint:

- Add summaries

- Add descriptions

- Add response descriptions

- Add request examples

- Add response examples

Ensure schemas display properly in Swagger UI.

README Updates

--------------

Update README.md with:

- Project overview

- Architecture overview

- Prerequisites

- Environment configuration

- Docker setup

- Migration commands

- Seed-data commands

- Running tests

- Accessing Swagger/OpenAPI documentation

Deliverables

------------

Provide:

- All newly created files

- All modified files

- Test coverage summary

- Seed data summary

- OpenAPI documentation summary

- README changes

---

# Prompt 2: Final Project Validation and Readiness Review

Perform a complete final review of the RBPDB backend project and verify implementation readiness.

Review the entire codebase against:

- Project specification

- ERD

- API requirements

- Database design

- Implemented functionality

Architecture Review

-------------------

Confirm:

- Layered architecture is consistently followed

- Routes remain thin

- Services contain business logic

- Repositories contain data access logic

- Dependency injection is used appropriately

Database Review

---------------

Verify:

- All ERD entities exist

- Relationships are implemented correctly

- Constraints are enforced correctly

- Alembic migrations work correctly

- Seed data can be loaded successfully

API Review

----------

Verify:

Users

Roles

Threads

Posts

Comments

For each resource confirm:

- CRUD operations implemented

- Correct status codes returned

- Request validation works

- Response schemas work

- OpenAPI documentation is complete

Testing Review

--------------

Review test coverage.

Identify:

- Missing tests

- Weak coverage areas

- Redundant tests

Provide an estimated coverage assessment by feature area.

Documentation Review

--------------------

Verify:

- README is complete

- Environment setup instructions are accurate

- Migration commands are correct

- Seed-data instructions are correct

- Swagger UI documentation is complete

Production and Grading Readiness

--------------------------------

Identify:

- Code quality concerns

- Technical debt

- Inconsistencies

- Missing functionality

- Potential grading risks

Generate a final readiness matrix:

| Area | Status | Notes |

|--------|--------|--------|

| Database Schema | Pass/Fail | |

| Migrations | Pass/Fail | |

| Pydantic Schemas | Pass/Fail | |

| User API | Pass/Fail | |

| Role API | Pass/Fail | |

| Thread API | Pass/Fail | |

| Post API | Pass/Fail | |

| Comment API | Pass/Fail | |

| Tests | Pass/Fail | |

| Seed Data | Pass/Fail | |

| OpenAPI Docs | Pass/Fail | |

| README | Pass/Fail | |

Provide a final list of recommended fixes, ordered by priority, before project submission.

## Why these prompts work

At this stage, you are no longer building new features. You're preparing the project for **grading, demonstration, and maintenance**.

**Prompt 1** is implementation-focused. It tells the agent to identify gaps and finish incomplete testing, seed data, and documentation rather than recreating work that already exists.

**Prompt 2** acts like a senior code review. It forces the agent to evaluate the entire project holistically against the specification, architecture, database, APIs, and documentation. This is often where AI agents catch missing OpenAPI examples, incomplete test coverage, orphaned endpoints, and README inconsistencies that could otherwise cost points during evaluation.

Together, these two prompts are typically sufficient to complete the final milestone without unnecessary prompt fragmentation.