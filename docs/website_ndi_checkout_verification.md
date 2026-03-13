## Checkout Flow
This flow is used when a customer is already logged in and starts NDI verification during checkout.
The purpose is not to log the user in again, but to:
  - verify identity during checkout
  - link Bhutan NDI to the existing account if not already linked
  - update only empty customer fields
  - return the user back to checkout
    
#### 1. User is already logged in
The customer already has an Odoo account session and is in the website checkout process.

At this point, the system knows who the current user is.

#### 2. User starts NDI from checkout
From the checkout page, the user is sent to:
  {/ndi/login?redirect=/shop/checkout}

This redirect value tells the system that the NDI process was started from checkout.

#### 3. System sets checkout flow type
When the NDI page opens, the redirect controller checks the redirect target.

If:
  - redirect is /shop/checkout
  - and the user is already logged in
then the session flow is set to:
  - checkout_verify

The target redirect URL is also saved in session so the user can be sent back to checkout after success.

#### 4. Proof request is created
When the user clicks to create the proof request, the system creates an NDI proof request and saves a login attempt record.

The attempt stores things like:
  - proof thread ID
  - session ID
  - flow type = checkout_verify
  - current logged-in user ID

This connects the checkout verification attempt to the correct account.

#### 5. Requested proof depends on whether NDI is already linked
Case A: user already linked with NDI
If the logged-in user already has an ndi_cid, the system requests only:
  - CID / ID Number

This is enough to confirm that the wallet belongs to the same person.

Case B: user not yet linked with NDI
If the account is not yet linked, the system requests full identity details such as:
  - CID
  - full name
  - mobile number
  - email
  - address fields

This allows the account to be linked and missing profile data to be filled.

#### 6. QR code is shown
The proof request URL is turned into a QR code.
The customer scans it using the Bhutan NDI wallet and approves the request.

#### 7. NDI sends webhook result
After the wallet approval, Bhutan NDI sends the proof result to the webhook.
The webhook matches the response using the saved thread_id.

#### 8. Webhook processes checkout verification
The webhook checks that the attempt is a checkout_verify flow.
Then it works with the already logged-in user tied to that attempt.
If the user is not yet linked to NDI
  - the scanned CID is checked
  - system ensures that this CID is not already linked to another account
  - if safe, the CID is saved on the current user
  - user is marked as NDI verified

If the user is already linked to NDI
  - the scanned CID must match the user’s existing linked CID
  - if it does not match, verification fails
  - if it matches, verification succeeds

This prevents one person from verifying checkout using someone else’s wallet.

#### 9. Empty user and partner fields are updated
After successful verification, the system updates user and partner details.

But it updates only empty fields, such as:
  - name
  - email
  - phone
  - mobile
  - street
  - city
  - state
  - country
  - postal code

This means existing checkout information is not overwritten unnecessarily.

#### 10. Attempt is marked validated
The proof attempt record is updated with:
  - validated status
  - CID
  - name
  - mobile
  - email
  - linked user ID
  - raw payload details

If this was the first time linking the wallet, the system also stores that information.

#### 11. Frontend polls verification status
The browser keeps polling /ndi/login/status.
When the attempt becomes validated, the status endpoint responds with success.

For checkout flow:
  - it does not create a new login session
  - it does not log the user in again
  - it returns a redirect back to /shop/checkout

#### 12. User returns to checkout
The user is redirected back to the checkout page.

Possible messages include:
  - Identity verified and linked to your account. Redirecting to checkout...

Verification successful. Redirecting to checkout...

So the final experience is smooth and stays within checkout.
