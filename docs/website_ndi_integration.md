# New user registration and login flow
When a person uses Bhutan NDI for the first time and there is no matching Odoo account, the system does two things in one flow:
  - registers the person as a new user
  - logs them in automatically

So from the user’s point of view, they do not need to manually sign up first.

## What identifies the user
  - The main identity used by the system is the user’s CID from Bhutan NDI.
  - That CID is the most important value because it uniquely connects the wallet holder to one Odoo account.
    
Other details like:
  - full name
  - mobile number
  - email
  - address
are used to fill the account profile, but CID is the real identity key.

## What happens when the user scans for the first time
#### Step 1: User scans QR
The user opens the Bhutan NDI wallet and scans the QR code shown on the Odoo page.

#### Step 2: User approves sharing identity
The wallet sends verified identity information back through the NDI process.

#### Step 3: Odoo receives verified data
The system receives verified attributes such as:
  - CID
  - full name
  - mobile number
  - email
  - address fields

#### Step 4: System checks whether user already exists
The system first tries to find an existing user.

Typical matching logic is:
  - first by NDI CID
  - if needed, by email/login

if still not found, it treats the person as a new user

#### Step 5: A new Odoo user is created
If no matching user exists, Odoo creates a brand new account for that person.

What credentials does the new user get?
Even though the user is signing in with NDI, Odoo still needs an internal account with login credentials.
1. Login username: The system creates a username using this priority:
  - email, if available
  - otherwise mobile number
  - otherwise a fallback like ndi_CID

Example:
email available → sonam@example.com
no email, mobile available → 17123456
neither available → ndi_11501001234

So yes, a username is created internally.

2. Password
  - The system generates a random password automatically.
  - This password is mainly for Odoo’s internal account requirement.
  - The user usually does not need to know it, because their normal authentication method is the NDI wallet scan.

Does the user need to enter email and password later
  - Normally, no.

For later sign-ins, the user can simply:
  - go to NDI login
  - scan the QR
  - approve in wallet
  - get logged in

The system reads the CID again and connects it to the already-created account.

So the real practical credential is:
  - NDI wallet ownership
  - and the verified CID
  - not the random password.

What happens immediately after registration
After the new user is created, the system does not stop at registration.

It also:
  - marks the user as NDI verified
  - stores the CID on the user account
  - updates available profile details
  - creates an Odoo session
  - logs the user in automatically

So the flow is:
  {scan → verify → register → login}

not:
  {scan → register only → ask user to log in manually}

What data is saved for the new user

The system usually saves:
  - On the user account
  - NDI CID
  - verified status
  - name
  - email if available

On the related contact/partner record
  - name
  - email
  - phone/mobile
  - street
  - city
  - state
  - country
  - postal code

This helps the account already have useful customer information after first verification.

Why a random password is still created?
Because Odoo user accounts generally require a login structure behind the scenes.

Even if your business flow is passwordless, the platform still needs:
  - a login field
  - a password field

So the password exists technically, but the user’s real access method is NDI.

What the user experiences?
For a brand new user, the experience is:
  - Open NDI login page
  - Scan QR with Bhutan NDI wallet
  - Approve identity sharing
  - System creates account automatically
  - System logs the user in
  - User is redirected into the website

The user may feel like “I logged in with NDI,” but in the background it was actually:
  - account creation
  - then login

What happens on future logins?
Next time the same person scans:
  - the system finds the existing account using the stored ndi_cid
  - no new account is created
  - the user is logged in directly

So first time:
  - create + login

Later times:

login only
