# FastAPI Full Course

This repo is my walkthrough of [Corey Schafer's FastAPI tutorial series](https://www.youtube.com/watch?v=iukOehU5aF4&t=25188s). I'm starting out in web development and wanted a solid, end-to-end project to learn how modern Python backends are built, from a first route all the way to production deployment.

## What I Learned

### 1. Getting Started : Web App + REST API

- Setting up a FastAPI project
- First routes returning JSON
- Automatic API documentation
- Serving a simple HTML response

### 2. HTML Frontend for Your API : Jinja2 Templates

- Jinja2 templates and layout inheritance
- Serving HTML pages alongside the API
- Static files and basic styling
- A styled blog homepage

### 3. Path Parameters : Validation and Error Handling

- Dynamic routes with path parameters
- Automatic type validation
- Individual post pages
- Proper error handling for API and browser clients

### 4. Pydantic Schemas : Request and Response Validation

- Request and response schemas
- Field-level validation
- Creating posts through the API

### 5. Adding a Database : SQLAlchemy Models and Relationships

- SQLAlchemy and a SQLite database
- User and Post models with relationships
- Database sessions via dependency injection
- Persisting data instead of keeping it in memory

### 6. Completing CRUD : Update and Delete

- Updating posts (PUT / PATCH)
- Deleting posts
- Full create, read, update, and delete flow

### 7. Sync vs Async : Converting the App to Asynchronous

- Async routes and database access
- When sync vs async makes sense

### 8. Routers : Organizing Routes into Modules

- Splitting routes into modules
- Cleaner project structure with routers

### 9. Frontend Forms : Connecting JavaScript to the API

- Forms that talk to the API
- Creating and updating posts from the browser

### 10. Authentication : Registration and Login with JWT

- User registration and login
- Password hashing
- JWT-based authentication

### 11. Authorization : Protecting Routes and Verifying the Current User

- Protected routes and the current user
- Account page
- Restricting actions to authorized users

### 12. File Uploads : Image Processing, Validation, and Storage

- Profile picture uploads
- Image processing and validation
- Secure local file storage

### 13. Pagination : Loading More Data with Query Parameters

- Query parameters for pagination
- Loading more posts from the UI
- Seeding the database with sample data
