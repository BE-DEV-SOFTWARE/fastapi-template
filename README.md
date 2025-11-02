# FastAPI Backend template

Hey! Ever wanted to get a custom backend up and running in a couple of minutes? Well you're in the right place! 

Using FastAPI and based on [fullstack example project of Tiangolo](https://github.com/tiangolo/full-stack-fastapi-postgresql), this templates allows you to focus on your features with an organized and highly opinionated structure.

Here is what you will be able to find out the box here:

- 🚀 OAuth2.0: Authentication by JWT with access Token and refresh Token
- 🔐 OTP Authentication: One-time password authentication via email
- 🥸 SSO: pre-configured auth with Facebook, Github and Google
- 📧 Email service: delegated email service using SMTP
- 📜 MJML: email templating
- 💽 PostgreSQL/SQLAlchemy: ORM managed database
- 🏁 Alembic: database migration
- 🗂️ File storage: file management on local disk
- 👾 UV: Rust based python package manager
- ✍️ CRUD: easy to setup and to replicate
- 🤖 Pytest: unit tests
- 🐳 Docker stack for development and deployment

## Requirements

* [Docker](https://www.docker.com/)
* [Docker Compose](https://docs.docker.com/compose/install/)
* [uv](https://docs.astral.sh/uv/) for Python package and environment management

## Deployment

This template provides with an out of the box Dockerized deployment on a VPS-like linux server using Traefik as a proxy. Simply update the env vars to match your project and follow the step-by-step [Deployment Documentation](./DEPLOY.md).

## Local development

### How to run the stack?
1. Create a `.env` file with initial value: 
    ```Bash
    cp env-example .env
    ```

2. Uncomment the variables to activate the services relevant to your project (e.g., email, file management, SSO credentials). For security, generate random strings for secret keys.

3. Once your `.env` file is configured, start the stack with Docker Compose:

    ```bash
    docker compose up -d
    ```

>[!TIP]
The first time you start your stack, it might take a bit of time to download all the docker images. While the backend waits for the database to be ready and configures everything. You can check the logs to monitor it.

To check the logs, run:

```bash
docker compose logs
```

To check the logs of a specific service, add the name of the service, e.g.:

```bash
docker compose logs backend
```

Perfect! We are done here 🙌 You can now open your favorite browser and interact with these URLs:

* http://localhost/api/ - FastAPI: REST API entry point

* http://localhost/docs - Swagger: Automatic interactive API documentation

* http://localhost:5050 - PGAdmin: PostgreSQL admin platform


### How to edit the code?

First install the python dependencies locally. Dependencies are managed with [uv](https://docs.astral.sh/uv/). You can install uv using pip or with their standalone installer:

```Bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

From the root folder of the project, install all the dependencies with:

```Bash
uv sync
```

That's it, ou are all set!

>[!TIP]
The current stack was already tested as is and we try to keep it up to date with the latest packages but if you want get all the latest and greatest of all the libraries you can simply run:
```Bash
uv sync --upgrade
```

If you are using VSCode you can simply open the root of the project using the `code` command:
```Bash
code .
```

>[!TIP]
The python virtual environment should be selected automatically in VSCode. If not, you can specify the path to your interpreter in the `.venv` folder created by the `uv sync` command.

### How to use the template?

Modify or add SQLAlchemy models in `./app/models/`, Pydantic schemas in `./app/schemas/`, API endpoints in `./app/api/`, CRUD (Create, Read, Update, Delete) utils in `./app/crud/`. The easiest might be to copy existing ones (models, endpoints, and CRUD utils) and update them to your needs. Don't forget to run a migration using alembic if you change the models.

This setup is designed to meet the needs of most applications. When your project starts to grow feel free to add new API versions, new routers or even new services to the `docker-compose.yml` files. Keep in mind that since this is a python backend, any python library will be compatible with this stack. Linear algebra with Numpy, ML and AI with Sci-Py, Image manipulation with Pillow or OpenCV... the possibilities are endless - let your creativity shape your next big feature! 🚀

### Docker Compose files

The main `docker-compose.yml` file is tailored for development, automatically used by `docker compose`. It enables features like source code mounting and hot-reload via the `start-reload.sh` script but does not include the Traefik service.  

For deployment, the `docker-compose.prod.yml` file is used, invoked by the `deploy.sh` script. Both Compose files rely on the `.env` file to inject environment variables into the containers.

## Testing

### Test during development

To test the backend during development on your local machine, make sure your docker stack is running:

```bash
docker compose up -d
```

Then proceed with running the test.sh script
```Bash
sh ./scripts/test.sh
```

### Test Coverage

Because the test scripts forward arguments to `pytest`, for example:
- ` --cov=app --cov-report=html` to enable test coverage HTML report generation
- `-x` to stop the tests at the fist failing test, which can be useful for debugging.
- `-k "test_api_users"` to run test that are matching the provided string, this can come in handy to isolate a given test or a group of tests.

To run the local tests with coverage HTML reports:

```Bash
sh ./scripts/test.sh --cov=app --cov-report=html
```

### Continuous testing

All tests specified in the `./app/tests` directory are automatically running when pushing or opening a PR to `dev` or `main` branch. You can of course add or modify the GitHub actions in `./.github/workflows` directory according to your needs.

## Migration

During local development, your app directory is mounted as a volume inside the container. This setup allows you to run `alembic` commands directly inside the container, and the migration files will be saved in your app directory. This makes it easy to track them in your Git repository.

### Steps for Database Migration

#### 1. Generate a Revision
   Whenever you make changes to your models (e.g., adding a column), you need to create a new migration revision. Simply run:  
   ```Bash
   sh ./scripts/new-revision.sh -m "Description of your revision"
   ```
   This command generates a migration script in the `./alembic/versions` directory based on your changes. **Don't forget about double checking any migration scripts before applying them.**

#### 2. Apply the Migration
    After creating the revision, apply the changes to the database by running:
    ```Bash
    sh ./scripts/migrate.sh
    ```
    This will update your database schema to match the changes in your models.


>[!IMPORTANT]
 If you created a new model in `./app/models/`, make sure to import it in `./app/db/base.py`, that Python module (`base.py`) that imports all the models will be used by Alembic.

>[!IMPORTANT]
 Remember to add and commit to the git repository the files generated in the alembic directory.

If you don't want to use migrations at all, uncomment the following line in the file `./app/db/init_db.py`:

```python
Base.metadata.create_all(bind=engine)
```

and comment the following line from the `prestart.sh` script:

```Bash
alembic upgrade head
```

>[!TIP]
If you want to start your migration history from scratch, you can remove all the revision files (`.py` Python files) in `./alembic/versions/`. And then create an initial migration as described above.

## Authentication

This template supports multiple authentication methods:

### Username/Password Authentication
Traditional email and password authentication using secure password hashing.

### OTP (One-Time Password) Authentication
Users can request a verification code via email to log in without a password. The verification code is a 6-digit number that expires after 10 minutes (configurable via `VERIFICATION_CODE_EXPIRATION_MINUTES`).

**Unified Login/Register Experience:**
Based on extensive user testing and client feedback, the OTP authentication endpoint automatically handles both login and registration. When a user provides a valid verification code:
- If the user exists: they are logged in
- If the user doesn't exist: a new account is automatically created and they are logged in

This creates a seamless experience similar to social media authentication (e.g., "Continue with Google"), where users don't need to choose between "Sign In" or "Sign Up". The frontend can still present separate Login and Register pages for user confidence and familiarity, but the backend gracefully handles both scenarios - missing accounts are created automatically, and existing accounts are logged in, regardless of which page the user started from.

To customize this behavior, you can edit the `authenticate_or_register_with_otp` function in the auth endpoints.

**Development Mode:**
- If email service is not configured (`EMAILS_ENABLED=False`), the verification code is returned in the API response for easy development and testing.
- You can inspect the verification code in the response using network inspection tools like Proxyman (for iOS apps) or browser DevTools Network panel (for web apps).
- A persistent OTP is available in development/staging environments (default: `123456`, configurable via `PERSISTENT_OTP`). This allows quick login for testing but **cannot be used to register new users** since it doesn't hold any user data - it only works for existing users.

### Apple Review Team OTP
For iOS app submissions, Apple's review team needs to test your app's authentication. A special persistent OTP system is available for this purpose:
- Admins can generate a persistent OTP via `/generate-apple-review-team-otp` endpoint
- The OTP is valid for 15 days (configurable via `APPLE_REVIEW_TEAM_OTP_EXPIRATION_DAYS`)
- The OTP works with the Apple review team user account (email: `review@apple.com` by default, configurable via `APPLE_REVIEW_TEAM_EMAIL`)
- Apple reviewers can use any email ending with `@apple.com` with this OTP to authenticate
- After review is complete, admins should delete the OTP via `/delete-apple-review-team-otp` endpoint for security
- The Apple review team email cannot request regular verification codes through the standard endpoint

## Emails

This template uses an email forwarding service (Brevo) for sending transactional emails. For detailed documentation on email configuration, templates, and best practices, see [EMAIL.md](./EMAIL.md).

**Quick Setup:**
- Get a free Brevo account at [https://www.brevo.com/](https://www.brevo.com/) (300 emails/day free)
- Add your API key and email configuration to `.env`
- Email templates are built with [MJML](https://mjml.io/) for full design control

## File storage/management

This template implement local storage of files. This means that the files like profile pictures, documents or other files you decide to implement in your future project will be stored on the local disc of the running server. Those files are persisted using docker volume. Although it's a great method to store files for a small project or during development to avoid setting up any extra configuration, it is highly encourage to replace this by a dedicated S3 object storage for your production builds.

# 🌟2025🌟 Roadmap:

Here you will find all the features that are planned to be progressively added in the upcoming year. The template is actively maintained and will be upgraded to get all the latest upgrades from its main libraries. Contributions are warmly welcome so don't hesitate to use it and share it! 😊
- **[⏳ In progress]** S3 simplified connection
- **[💭 To be considered]** Update to utilize Async technology (for endpoints that can benefit from it) https://medium.com/@neverwalkaloner/fastapi-with-async-sqlalchemy-celery-and-websockets-1b40cd9528da#:~:text=Starting%20from%20version%201.4%20SQLAlchemy,let's%20start%20with%20database%20connection. https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **[💭 To be considered]** Migration to psycopg v3 could be considered in a future version of the template

## Notes from the author

### ⛔️ Warning about scalability

This template is optimized for deployment on a single VPS or server, providing an easy-to-use solution for small to mid-size projects. The `docker-compose.prod.yml` file offers a comprehensive development setup (including DB, file storage, pgAdmin, etc.) that works well for testing or small-scale deployments. However, it is not optimized for Kubernetes or large-scale production environments out of the box. While it remains production-ready and ideal for simple, manageable structures, it is not designed to scale efficiently for larger or more complex systems.

### License and commercial use

This template is Open-Sourced under the MIT license. This basically means that all contributions are welcome and encouraged. You can use this template or fork it for your personal and commercial use 🥳

If you have questions or encounter any difficulty while using this repo do not hesitate to use the GitHub Discussions channel.

If you need help on your project or look for a commercial collaboration please reach out to me by email [jonathan@be-dev.ch](mailto:jonathan@be-dev.ch) or check [the BE-DEV team website: be-dev.ch](https://be-dev.ch)
