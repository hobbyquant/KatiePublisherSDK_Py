# Katie Publisher SDK - JavaScript

A JavaScript/TypeScript SDK for publishing voice messages to Katie channels.

> **Status:** Coming Soon

This SDK is planned for use with:
- Node.js applications
- Browser-based publishers
- Zapier/Make/n8n integrations

## Planned Features

- ES Module and CommonJS support
- TypeScript definitions included
- Promise-based API
- `publish()` and `broadcast()` methods
- Configurable timeout and retry logic

## Planned Usage

```javascript
import { MessagingClient } from '@katie/publisher-sdk';

const client = new MessagingClient({
  baseUrl: 'https://katiespeaker.com',
  channelApiKey: 'your-channel-api-key'
});

// Publish a message (subscribers can filter)
await client.publish('Hello, World!');

// Publish with metadata for filtering
await client.publish('Bitcoin price alert', {
  ttlSeconds: 60,
  meta: { asset: 'BTC', price: 50000 }
});

// Broadcast to ALL subscribers (bypasses filters)
await client.broadcast('Emergency announcement');
```

## Contributing

Contributions welcome! See the main repository for guidelines.
