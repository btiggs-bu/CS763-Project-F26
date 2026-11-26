# Pydantic API Schema Plan

This plan describes the Pydantic schemas for the API documented in
[`spec.md`](../spec.md). The schema families are implemented in
[`functional_codebase/app/schemas/`](../functional_codebase/app/schemas/).

## Conventions

- Use Pydantic 2 models. Response models read ORM objects with
  `from_attributes=True`.
- Use `EmailStr` for user email; `email-validator` is a runtime dependency.
- PATCH schemas are partial: every field is optional, omitted fields remain
  unchanged, and an empty update should be rejected.
- Validation covers the request's shape and field constraints. Existing-record
  uniqueness, foreign-key existence, subtype hierarchy, and same-post comment
  parent checks remain database/service concerns.
- `user_id` values remain client-supplied for create requests until
  authentication is implemented.
- Response relationships are represented as simple values rather than nested
  ORM graphs: roles and tags are string lists, and thread hierarchy is exposed
  as nullable `parent_thread_id`.
- Collection responses use `ListResponse[T]` with required `count: int` and
  `results: list[T]`.
- All normal entity responses include non-null `created_at` and `updated_at`.
  `UserRead.deleted_at` is nullable.
- DELETE operations return HTTP 204 with no body and therefore have no
  Pydantic response schema.

## Implemented Inheritance

- `Schema` provides Pydantic configuration, including `from_attributes=True`,
  to the schema families. `TimestampedRead` adds the common timestamp fields.
- `UserProfileBase` defines email and display name. `UserBase` extends it with
  username; `UserCreate` and `UserRead` extend `UserBase`. `UserRead` also
  inherits `TimestampedRead`. `UserUpdate` inherits both `UserProfileBase` and
  `PatchSchema`, omitting username because it is immutable.
- `ThreadBase` defines the common thread fields. The three subtype create
  schemas inherit a shared create base, which adds `user_id`; their literal
  `thread_type` fields form the discriminated `ThreadCreate` union.
  `ThreadRead` extends `ThreadBase` and `TimestampedRead`;
  `ThreadUpdate` extends `ThreadBase` and `PatchSchema`.
- `PostBase` defines title, content, and restriction level. `PostCreate` and
  `PostRead` extend it (`PostRead` also extends `TimestampedRead`), while
  `PostUpdate` extends `PostBase` and `PatchSchema` so immutable fields are
  not accepted.
- `CommentBase` defines content. `CommentCreate` and `CommentRead` extend it
  (`CommentRead` also extends `TimestampedRead`); `CommentUpdate` extends
  `CommentBase` and `PatchSchema`.
- `TagBase` defines the constrained tag name. `TagCreate` and `TagRead` extend
  it; `TagUpdate` extends `TagBase` and `PatchSchema`.
- All update schemas share `PatchSchema`, which rejects empty updates and
  explicit nulls for non-nullable fields.

## User and Role

| Schema | Fields | Required and validation |
|---|---|---|
| `UserCreate` | `username`, `email`, `display_name`, `roles` | Username 3–50 characters; valid email up to 254 characters; display name 1–100 characters. `roles` is an optional list of `student`, `faculty`, or `admin`. |
| `UserPatch` | `email`, `display_name`, `roles` | All optional; same constraints as create. `username` is not patchable under the current API contract. |
| `UserRead` | `user_id`, `username`, `email`, `display_name`, `roles`, `created_at`, `updated_at`, `deleted_at` | All fields are present; `deleted_at` may be null. |
| `UserList` | `count`, `results: list[UserRead]` | Standard list wrapper. |

Roles are exposed as strings, not nested role objects. The database role
lookup and `USER_ROLE` assignment table have no standalone routes or request
schemas. The service must ensure each user has at least one role; if roles are
omitted or empty, it assigns `student`.

## Threads and Subtypes

`ThreadType` is an enum with the singular values `lab`, `course`, and
`project`. The create schema should be a discriminated union of
`LabThreadCreate`, `CourseThreadCreate`, and `ProjectThreadCreate`, keyed by
`thread_type`; these share the same fields but make each allowed type explicit.

| Schema | Fields | Required and validation |
|---|---|---|
| `LabThreadCreate` | `thread_type="lab"`, `user_id`, `name`, `description`, `restriction_level`, `tags` | `user_id`, `name`, and `restriction_level` required. Name 1–200 characters; description optional, max 5000; restriction is `open`, `restricted`, or `closed`; tags optional string list. Labs cannot have a parent. |
| `CourseThreadCreate` | `thread_type="course"`, `user_id`, `name`, `description`, `restriction_level`, `parent_thread_id`, `tags` | Same field constraints; parent is optional and, if supplied, must be a lab thread. |
| `ProjectThreadCreate` | `thread_type="project"`, `user_id`, `name`, `description`, `restriction_level`, `parent_thread_id`, `tags` | Same field constraints; parent is optional and, if supplied, must be a course thread. |
| `ThreadPatch` | `name`, `description`, `restriction_level`, `parent_thread_id`, `tags` | All optional. `parent_thread_id` may be null to remove an existing parent where allowed; hierarchy rules still apply. `thread_type` and creator are immutable. |
| `ThreadRead` | `thread_id`, `user_id`, `thread_type`, `name`, `description`, `restriction_level`, `parent_thread_id`, `tags`, `created_at`, `updated_at` | All fields are present; `description` and `parent_thread_id` may be null. |
| `ThreadList` | `count`, `results: list[ThreadRead]` | Standard list wrapper. |

The subtype name and description are flattened into the API thread schema;
clients do not submit database subtype records or `THREADS_GROUP` rows. The
nullable `parent_thread_id` is the API projection of that relationship.

## Posts

| Schema | Fields | Required and validation |
|---|---|---|
| `PostCreate` | `post_type`, `user_id`, `thread_id`, `title`, `content`, `restriction_level`, `tags` | `post_type` is `announcement` or `discussion`; IDs, title (1–200), and content (1–10000) are required. Restriction is optional and defaults to `inherited`; tags are an optional string list. `mod_status` is server-managed and defaults to `active`. |
| `PostPatch` | `title`, `content`, `restriction_level` | All optional; same length and enum constraints. Author, thread, type, and moderation status are not client-editable here. Tags are not in the current PATCH request contract and remain unchanged. |
| `PostRead` | `post_id`, `post_type`, `user_id`, `thread_id`, `title`, `content`, `restriction_level`, `mod_status`, `tags`, `created_at`, `updated_at` | All required. |
| `PostList` | `count`, `results: list[PostRead]` | Standard list wrapper. |

Announcement authorization and whether an explicitly supplied restriction
level may be changed are service-layer rules, not schema-only validation.

## Comments

| Schema | Fields | Required and validation |
|---|---|---|
| `CommentCreate` | `user_id`, `p_comment_id`, `content` | `user_id` and content (1–5000 characters) required; `p_comment_id` optional. `post_id` comes from the URL and is not duplicated in the request body. Restriction and moderation status are server-managed. |
| `CommentPatch` | `content` | Optional, 1–5000 characters; reject an empty PATCH. |
| `CommentRead` | `comment_id`, `user_id`, `post_id`, `p_comment_id`, `content`, `restriction_level`, `mod_status`, `created_at`, `updated_at` | All fields are present; `p_comment_id` may be null. `restriction_level` is included in reads and defaults to `inherited`; it is not client-settable. |
| `CommentList` | `count`, `results: list[CommentRead]` | Standard list wrapper. |

The database enforces that a parent comment belongs to the same post. The
service must preserve that invariant when validating `p_comment_id`.

## Moderation, Filters, and Timeline

- `ModerationStatusUpdate`: required `mod_status`, restricted to
  `active`, `reported`, or `hidden_by_moderator`; used by moderation PATCH
  endpoints.
- `ModerationResult`: the resource identifier, `mod_status`, and
  `updated_at`; report PATCH endpoints take no request body.
- Query parameters are optional filters and should have typed query models:
  user filters (`role_id`, `thread_id`); thread filters (`user_id`,
  `thread_type`, `restriction_level`, `tag_id`, `parent_thread_id`); post
  filters (`keyword`, `thread_id`, `user_id`, `post_type`, `tag_id`,
  `mod_status`); and comment filters (`keyword`, `user_id`, `mod_status`,
  `format`, restricted to `json` or `txt`, defaulting to `json`). For
  `format=json`, the response is the Pydantic `CommentList`. For `format=txt`,
  return a raw downloadable `PlainTextResponse`
  (`text/plain; charset=utf-8`, `Content-Disposition: attachment`); that
  branch intentionally has no Pydantic JSON response model. The endpoint
  should branch on the validated query value rather than applying the
  `CommentList` response model to both formats.
- `thread_type` path values for timeline requests are singular: `project`,
  `course`, or `lab`. Timeline results use the post response schema and list
  wrapper.

## Entities Without Standalone API Schemas

`Role`, `UserRole`, `UserThread`, `ThreadTag`, and `PostTag` have no standalone
routes in the current API. Roles are represented as role-name strings,
membership as user/thread IDs, and thread hierarchy as `parent_thread_id`.
`Tag` has reusable base/create/update/read schemas for validation and
serialization, although no standalone tag endpoints are currently specified.

## Errors and Health

The error response model must match the installed exception handlers exactly:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed"
  },
  "timestamp": "2026-11-02T11:06:07.235541+00:00",
  "request_id": "0f45ef7d-790a-4b82-b9fc-fd2c8afc8d5b"
}
```

`ErrorEnvelope` contains `error`, `timestamp`, and `request_id`; its nested
error contains only `code` and `message` (no `details`). Codes are
`VALIDATION_ERROR`, `HTTP_ERROR`, `DATABASE_ERROR`, and
`INTERNAL_SERVER_ERROR`.

`HealthRead` contains `status: "healthy"` for successful `/health` and
`/health/db` responses. A database-health failure returns HTTP 503 with the
standard error envelope, code `HTTP_ERROR`, and message `Database unavailable`.
