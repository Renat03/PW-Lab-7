# 🏋️ Workout Tracker API

This is a FastAPI-based CRUD API for managing workouts, exercises, and sets. It supports authentication, role-based authorization, and provides a simple in-memory data store for demonstration purposes.

---

## 🚀 Features

- 🔐 JWT-based authentication with `OAuth2PasswordBearer`
- 🧑‍💼 Role-based access control (READ / WRITE / DELETE permissions)
- 📋 Full CRUD support for:
  - Workouts
  - Exercises
  - Exercise Sets
- 📄 Auto-generated API docs with Swagger UI
- 🗃️ Pagination support for workouts list

---

## 🔐 Authentication

### Login

Use the `/token` endpoint to obtain a Bearer token using form data.


## 📦 API Endpoints

### Auth

#### `POST /token`
Obtain access token using form data:
- `username`: `admin` or `user`
- `password`: `secret`

---

### Workouts

#### `GET /workouts/`
List workouts (with pagination).  
🔐 Requires `READ` permission.

Query Parameters:
- `skip`: int (default: 0)
- `limit`: int (default: 10)

#### `POST /workouts/`
Create a new workout.  
🔐 Requires `WRITE` permission.

Example JSON body:
```json
{
  "name": "Leg Day",
  "date": "2025-06-04",
  "startTime": "18:00",
  "endTime": "19:00",
  "rating": 8,
  "comment": "Strong session"
}
```

#### `GET /workouts/{workout_id}`

Retrieve a specific workout.
🔐 Requires READ permission.

#### `PUT /workouts/{workout_id}`

Update an existing workout.
🔐 Requires WRITE permission.


#### `DELETE /workouts/{workout_id}`

Delete a workout.
🔐 Requires DELETE permission.


### Exercises

#### `POST /workouts/{workout_id}/exercises`

Add an exercise to a workout.
🔐 Requires WRITE permission.

```json
{
  "name": "Squat",
  "category": "Legs"
}
```


### Sets

#### `POST /workouts/{workout_id}/exercises/{exercise_id}/sets`

Add an exercise to a workout.
🔐 Requires WRITE permission.

```json
{
  "reps": 12,
  "weight": 80.0
}
```