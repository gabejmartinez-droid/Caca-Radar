# Caca Radar - PRD

## Architecture
- **Frontend:** React 19 + TailwindCSS + Shadcn UI + Leaflet + PWA
- **Backend:** FastAPI + MongoDB + Object Storage + Resend + Apple/Google webhooks
- **Services:** scoring, antispam, validation, ranking, email, webhook_handlers

## Test Credentials
- Admin: admin@cacaradar.es / admin123
- Municipality: madrid@cacaradar.es / madrid123

## Webhook URLs (configure in App Store Connect / Google Play Console)
- Apple: POST /api/webhooks/apple
- Google: POST /api/webhooks/google  
- Status: GET /api/webhooks/status

## Environment Variables for Production
```
RESEND_API_KEY=re_your_key (from resend.com)
SENDER_EMAIL=no-reply@cacaradar.es
APPLE_BUNDLE_ID=com.cacaradar.app
APPLE_KEY_ID=your_key_id
APPLE_ISSUER_ID=your_issuer_id
APPLE_KEY_PATH=/path/to/AuthKey.p8
GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json
GOOGLE_PACKAGE_NAME=com.cacaradar.app
```

## All Implemented Features
- Map with color-coded pins, 8 languages, RTL Arabic
- Reports with GPS, photo, description, anti-spam
- Gamification: scoring, trust, validation, rankings
- Municipality auto-tagging, dashboard, self-registration with domain verification
- Subscriptions with Apple/Google receipt verification
- Webhooks for real-time subscription status updates
- Email service for verification codes (Resend)
- PWA manifest + service worker
- Content moderation with flag reasons
