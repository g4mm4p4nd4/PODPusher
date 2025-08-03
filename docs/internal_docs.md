# Internal Documentation

## Social Media Generator Service

The `social_generator` service provides an endpoint to create social media
content from a text prompt. It returns a marketing caption and an image URL.

### API

- **POST `/social/post`**
  - Body: `{ "prompt": string }`
  - Response: `{ "caption": string, "image_url": string }`

Behind the scenes the service calls the OpenAI integration client. When the
`OPENAI_USE_STUB` environment variable is set or `OPENAI_API_KEY` is missing,
stubbed responses are returned. The integration client implements basic retry
logic for rate limits.

### Flow

```mermaid
flowchart LR
    A[Prompt] --> B[OpenAI Caption]
    A --> C[OpenAI Image]
    B --> D[Social Post]
    C --> D
```

The task can also be executed asynchronously via the Celery task
`generate_social_post_task`.

## Frontend Page

The `/social-generator` page renders the `SocialMediaGenerator` component. Users
enter a prompt and the page displays the generated caption and image. The
component uses the shared translation files and the design system classes for a
responsive layout.
