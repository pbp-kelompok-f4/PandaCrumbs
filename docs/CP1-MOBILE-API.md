# CP1 mobile API — modules 1–2

Django REST Framework endpoints using the existing Django models and database.
These are read-only CP1 endpoints. Mobile CRUD, consume actions and bookmark
writes remain future work.

## Routes

| Module | List | Detail | Access |
| --- | --- | --- | --- |
| Smart Pantry | `/api/pantry/` | `/api/pantry/<id>/` | Current user's items only |
| Leftover Recipe | `/api/recipes/` | `/api/recipes/<id>/` | Public; personal tabs require login |

Keep trailing slashes. GET, HEAD and OPTIONS are supported. Lists return JSON
arrays without pagination, including `[]` when empty. Details return objects.
Missing IDs and another user's pantry item return 404. Anonymous private requests
return JSON 403 instead of a login redirect. Authenticated writes return 405.
The API does not change stock, recipes or bookmarks.

## Authentication

These endpoints inherit main's shared session authentication. POST JSON
`{"username": "your-username", "password": "your-password"}` to `/auth/login/`.
A successful response has `status: true`; preserve its `sessionid` cookie on
subsequent API requests. POST `/auth/logout/` to end the session. Flutter should
use the team's existing cookie-aware client (`pbp_django_auth`). A separate Safari
session does not authenticate Flutter. Use HTTPS on PWS.

The existing website login also works. This change does not modify shared auth,
CORS, cookie settings, or the modules 3–5 APIs. JSON rendering is selected only
on the new Pantry and Recipe views, without changing other modules' renderers.

## Team-standard routes

Use `/pantry/api/` and `/pantry/api/<id>/`, or `/recipes/api/` and
`/recipes/api/<id>/`, as listed in the main README. The `/api/pantry/` and
`/api/recipes/` routes above remain equivalent aliases, including filters and
permissions. Writes to either form return 405 for signed-in users.

## Pantry fields

`id`, `name`, `category`, `quantity`, `unit`, `location`, `expires_on`, `stored_on`,
`image_url`, `barcode`, `status`, `status_label`.

Dates are `YYYY-MM-DD`; quantity is an integer. Status comes from the existing
model: `expired` before today, `soon` from today through three days ahead
inclusive, and `safe` afterward. Owner selection is server-side; query parameters
cannot request another user's inventory. Pantry filtering is not included yet.

## Recipe fields and filters

`id`, `author` (user ID), `author_name` (username), `title`, `ingredients`, `steps`,
`portions`, `minutes`, `image_url`, `created_at`, `is_saved`.

Ingredients and steps remain newline-separated strings; split them into lines
for Flutter display. `created_at` is an ISO 8601 timestamp. Image URLs use the
saved external image first, then an absolute URL to the existing demo image,
otherwise an empty string. `is_saved` refers only to the current user's bookmark;
it is false for guests. No email, password or other users' bookmark data is exposed.

Supported query parameters (also apply to detail lookups):

- `tab=all` (default), `tab=mine`, or `tab=saved`. Unknown tabs behave as `all`.
  Personal tabs require login and scope results to the current user.
- `q=rice`: case-insensitive title or ingredient search (first 120 characters).
- Repeated `ingredient` parameters: each ingredient must match, for example
  `?ingredient=rice&ingredient=egg`. Up to 12 distinct values, 40 characters each.
- `quick=1`: strictly less than 30 minutes. Filters combine.

## Verification and release

Install `requirements.txt` in the project's virtual environment, then run:

```sh
python manage.py check
python manage.py test main.test_cp1_api
python manage.py test
python manage.py makemigrations --check --dry-run
node --test tests/js/*.test.cjs
```

Use a test database. No model changes or new migrations are introduced. Existing
migrations are still required for a fresh installation. These changes are local;
deploy the Django backend to PWS and verify live access before submitting its URLs.
Flutter implementation is separate.

Nine API tests and ten JavaScript tests passed. The full Django test run used
an isolated SQLite database: 165 tests, with the same 10 failures and 2 errors
observed before the API work (156 tests). This is not a clean full-suite result.

Pre-existing failures/errors — HabitChallengeTests (`habit_challenge.tests`):
- ERROR: `test_confirmation_uses_saved_food_and_does_not_reward_duplicate`
- ERROR: `test_cooking_confirmation_and_accessible_dialogs`
- FAIL: `test_ajax_checkin_updates_dashboard_and_escapes_food`
- FAIL: `test_checkin_validation_csrf_and_unknown_kind`
- FAIL: `test_database_guards_duplicates_and_invalid_rewards`
- FAIL: `test_empty_dashboard_and_navigation`
- FAIL: `test_plan_create_edit_checkin_delete_keeps_points`
- FAIL: `test_plan_ownership_and_checkin_kind_period`
- FAIL: `test_plan_validation_and_recorded_dates_are_preserved`
- FAIL: `test_progress_level_boundaries_and_streak_gap`
- FAIL: `test_server_rewards_once_per_kind_per_day`

ProductSearchContractTests (`main.tests`):
- FAIL: `test_normalized_query_and_product_fields_keep_existing_limits`
