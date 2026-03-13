# NDI-Integration-Odoo-Ecommerce
This repository contains custom Odoo modules that integrate Bhutan National Digital Identity (NDI) authentication and identity verification into an Odoo eCommerce platform.

## NDI Integration Guide
This section describes the process of integrating Bhutan National Digital Identity (NDI) authentication and verification into the system.

### NDI Integration Sequence
The following steps outline the workflow required to integrate with the Bhutan NDI verifier services.
1. Obtain Credentials: Request the following credentials from the NDI organization:
   - client_id
   - client_secret

2. Generate Access Token: Use the client_id and client_secret with the NDI Authenticator Service to generate an access token. This token must be included in all API requests.
  {Authorization: Bearer <access_token>}

4. Expose Local Development Server: Expose your local server so that NDI services can access your webhook endpoint.
Example using ngrok:
  {ngrok http 8069}
This will generate a public URL such as:
  {https://xxxx.ngrok.io}

4. Create a Webhook Endpoint: Create a webhook endpoint in your website to receive verification responses from the NDI service.
Example endpoint:
  {https://your-domain.com/ndi/webhook}

5. Register Webhook with NDI: Register your webhook endpoint with the NDI Webhook Service so the system can receive proof verification events.

6. Create Proof Request: Use the NDI Verifier Service to create a proof request.
This generates:
    - Proof Request URL
    - Deep Link URL
    - Thread ID
The Proof Request URL is used to generate the QR Code for the user to scan with their NDI Wallet.

7. Subscribe Webhook to Thread ID: Each proof request has a unique Thread ID.
Subscribe your webhook to the thread ID so your application receives verification updates when the user approves or rejects the request.

### Odoo Integration

The following configuration is required inside Odoo.
Navigate to:
  {Settings → Technical → System Parameters}

Add the following parameters:

Parameter	Description:
   - ndi.access_token - Access token generated using the authenticator service
   - ndi.base_url - Base URL for NDI API
   - ndi.schema_name - Schema used for identity verification
   - ndi.webhook_id - Unique webhook identifier
   - ndi.webhook_token	- Token used to validate webhook requests

