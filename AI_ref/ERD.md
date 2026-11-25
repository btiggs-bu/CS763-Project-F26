```mermaid
erDiagram
  USER {
    int user_id PK
    string username UK
    string email UK
    string display_name
    timestamp deleted_at "nullable; soft delete"
    timestamp created_at
    timestamp updated_at
  }
  ROLE {
    int role_id PK
    string role_name UK "student/faculty/admin"
  }
  USER_ROLE {
    int user_role_id PK
    int user_id FK
    int role_id FK
  }
  THREADS {
    int thread_id PK
    int user_id FK
    string thread_type "lab/course/project"
    string restriction_level "open/restricted/closed"
    timestamp created_at
    timestamp updated_at
  }
  PROJECT {
    int thread_id PK, FK
    string name
    string description
  }
  COURSE {
    int thread_id PK, FK
    string name
    string description
  }
  LAB {
    int thread_id PK, FK
    string name
    string description
  }
  USER_THREADS {
    int user_thread_id PK
    int user_id FK
    int thread_id FK
  }
  POST {
    int post_id PK
    string post_type "announcement/discussion"
    int user_id FK "author"
    int thread_id FK "root project/course/lab"
    string title
    text content
    string restriction_level "inherited/open/restricted/closed"
    string mod_status "active/reported/hidden_by_moderator"
    timestamp created_at
    timestamp updated_at
  }
  COMMENT {
    int comment_id PK
    int user_id FK "author"
    int post_id FK "parent post"
    int p_comment_id FK "nullable; parent comment on same post"
    string content
    string restriction_level "inherited/open/restricted/closed; default inherited"
    string mod_status "active/reported/hidden_by_moderator"
    timestamp created_at
    timestamp updated_at
  }
  TAG {
    int tag_id PK
    string tag UK
  }
  THREADS_GROUP {
    int thread_group_id PK
    int p_thread_id FK "thread id of parent course or lab"
    int c_thread_id FK, UK "thread id of child project or course"
  }
  THREADS_TAG {
    int thread_tag_id PK
    int thread_id FK
    int tag_id FK
  }
  POST_TAG {
    int post_tag_id PK
    int post_id FK
    int tag_id FK
  }
  USER ||--o{ THREADS : "creates"
  USER ||--o{ POST : "creates"
  USER ||--o{ COMMENT : "creates"
  USER ||--o{ USER_ROLE : "has"
  ROLE ||--o{ USER_ROLE : "describes"
  THREADS ||--o| PROJECT : "is a"
  THREADS ||--o| COURSE : "is a"
  THREADS ||--o| LAB : "is a"
  THREADS ||--o{ THREADS_GROUP : "contains or is part of"
  USER ||--o{ USER_THREADS : "belongs to"
  THREADS ||--o{ USER_THREADS : "includes"
  THREADS ||--o{ POST : "contains"
  POST ||--o{ COMMENT : "has"
  COMMENT ||--o{ COMMENT : "parent comment / replies"
  THREADS ||--o{ THREADS_TAG : "has"
  TAG ||--o{ THREADS_TAG : "describes"
  POST ||--o{ POST_TAG : "has"
  TAG ||--o{ POST_TAG : "describes"
```

### ERD constraints and lifecycle notes

- All `created_at` and `updated_at` columns are non-null. `created_at` defaults to the current timestamp; `updated_at` defaults to it and is refreshed whenever the row is updated.
- Use a database update trigger (or equivalent centralized persistence mechanism) to refresh `updated_at` consistently on updates.
- String-backed constrained values use database `CHECK` constraints rather than native database enums:
  - `ROLE.role_name`: `student`, `faculty`, `admin`
  - `THREADS.thread_type`: `lab`, `course`, `project`
  - `THREADS.restriction_level`: `open`, `restricted`, `closed`
  - `POST.post_type`: `announcement`, `discussion`
  - `POST.restriction_level` and `COMMENT.restriction_level`: `inherited`, `open`, `restricted`, `closed`
  - `POST.mod_status` and `COMMENT.mod_status`: `active`, `reported`, `hidden_by_moderator`
- `POST.mod_status` and `COMMENT.mod_status` default to `active`; `POST.restriction_level` and `COMMENT.restriction_level` default to `inherited`.
- Each `THREADS` row must have exactly one matching subtype row in `PROJECT`, `COURSE`, or `LAB`, matching `thread_type`. Enforce this with deferred database constraint triggers so a base row and its subtype can be inserted or changed in one transaction.
- A `THREADS_GROUP.c_thread_id` may occur only once, enforcing at most one parent per child. A database trigger enforces valid parent-child types (Lab-to-Course and Course-to-Project); self-parenting is prohibited.
- `COMMENT.p_comment_id` is nullable. When populated, the parent comment must belong to the same `post_id`; enforce this with a composite foreign key from `(p_comment_id, post_id)` to `(comment_id, post_id)` on `COMMENT`, with a corresponding unique constraint on `(comment_id, post_id)`.
- User deletion is soft deletion: set `USER.deleted_at`, and set the restriction level to `closed` for that user's created threads, posts, and comments. Do not cascade-delete those rows when a user is soft-deleted.
- Direct deletion of a thread or post cascades to dependent rows, including subtype, hierarchy, association/tag, post, and comment rows as applicable. Deleting a parent thread also deletes its child threads recursively; use a database trigger or an equivalent transactional deletion operation for this hierarchy behavior.
- User-role assignment must ensure each user has at least one role; when no role is supplied, assign the `student` role.