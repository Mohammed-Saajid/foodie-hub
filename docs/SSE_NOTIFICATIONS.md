# SSE Notifications

This project provides a Redis-backed SSE notification service for:

- User-specific notifications
- Role-specific notifications
- Group-specific notifications
- Broadcast notifications

## Stream Endpoint

- Method: `GET`
- Path: `/api/v1/notifications/stream`
- Auth: Bearer token required
- Optional query: `groups` (repeatable)

Example:

```bash
curl -N \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer <jwt>" \
  "http://127.0.0.1:8000/api/v1/notifications/stream?groups=daily-rush"
```

## Redis Channel Model

Base prefix: `notifications`

- Broadcast: `notifications:broadcast`
- User: `notifications:user:{user_id}`
- Role: `notifications:role:{role}`
- Group: `notifications:group:{group_name}`

When a client subscribes, it automatically listens to:

- Its user channel
- Its role channel
- Broadcast channel
- Requested group channels (normalized lowercase)

## Publish Endpoints (Admin)

- `POST /api/v1/notifications/publish/user/{user_id}`
- `POST /api/v1/notifications/publish/role/{role}`
- `POST /api/v1/notifications/publish/users`
- `POST /api/v1/notifications/publish/group/{group_name}`
- `POST /api/v1/notifications/publish/broadcast`

Request body for all publish endpoints:

```json
{
  "event": "order_created",
  "message": "New order available",
  "data": {
    "order_id": 123
  }
}
```

## Config

Defined in `app/core/config.py`:

- `NOTIFICATION_CHANNEL_PREFIX`
- `SSE_RETRY_MS`
- `SSE_HEARTBEAT_SECONDS`
- `SSE_POLL_TIMEOUT_SECONDS`
- `SSE_MAX_GROUPS_PER_CONNECTION`
