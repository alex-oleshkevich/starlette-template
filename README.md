# Welcome to the `starlette-template` documentation

This is a template project for a Starlette web application.
It is designed to be a solid starting point for a new project with a focus on security, scalability, and developer
experience.

> This is a work in progress. The documentation is not complete yet.
> The performance may not be optimal, and the security may not yet be perfect.

## The vision

There are a many other templates and frameworks out there, so why create another one?
Well, I wanted to have a template, that enables me to start a new project quickly,
without having to worry about the basic stuff like authentication, authorization, configuration, etc.
I also wanted to have a template that is easy to understand and extend, and that is based on modern technologies.

## Features

The project is based on Starlette library.

### Tech features

- **Project structure**: well organized project structure with a clear separation of concerns.
- **Configuration**: envvars based configuration with a sensible defaults.
- **Multiple environments**: support for multiple environments (development, testing, production) with an option to
  override configuration.
- **Database**: support for both sync and async database access using SQLAlchemy.
- **Testing**: good test coverage with various fixtures and a way to fux configuration for testing.
- **Docker**: includes Dockerfile and docker-compose for easy deployment.
- **Deployment**: deploy anywhere using GitHub Workflows and other CI/CD tools.
- **CLI tools**: various CLI tools for managing the application.
- **Emails**: support for sending emails using mail servers of your choice or services like SendGrid.
- **API endpoints**: support for API documentation using Swagger UI.
- **Logging**: structured logging with support for various log levels.
- **Prometheus metrics**: support for Prometheus metrics.
- **Background jobs**: support for background jobs using `saq`.
- **Event dispatching**: emit domain events to decorate the application with additional functionality.
- **Caching**: support for caching using configurable backends.
- **Sentry integration**: support for error tracking using Sentry.
- **Rate limiting**: support for rate limiting.
- **File uploads**: upload to local directory or S3 using file system abstraction.
- **Pagination**: paginate database queries.
- **Database query helpers**: common database operations made easy.

### Business features

- **Authentication**: support for email/password, JWT token, and social authentication.
- **Authorization**: powerful permission system with support for roles and permissions.
- **Stripe integration**: support for subscription plans and payments using Stripe.
- **User registration**: support for user registration with email verification.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/alex-oleshkevich/starlette-template.git
```

2. Install Python the dependencies:

```bash
poetry install
```

3. Install frontend dependencies:

```bash
npm install
```

4. Create a `.env` file:

```bash
touch .env
```

It is ok to have it empty at this stage since the project has sensible defaults.
Put any configuration overrides in the `.env` file.
