# DLMS Orders Feature

## Overview

DLMS (Device Lifecycle Management System) Orders are certificate provisioning orders for DLMS-compliant smart metering devices.

## Business Context

### What is DLMS?

DLMS (Device Language Message Specification) is a protocol standard for smart metering communication in the energy/utility sector.

**Business Problem it Solves:**

- Enables secure certificate provisioning for smart metering devices
- Provides manufacturer identity and device authentication for utility meters
- Ensures secure communication between utility meters and utility companies

**Why Customers Need DLMS Orders:**

- Meter manufacturers need certificates to authenticate their devices
- Utilities require verified device identities for secure meter-to-head-end communication
- Compliance with smart metering security standards

**Industry Standards:**

- DLMS/COSEM protocol for smart metering
- X.509 certificate-based security
- ISO 3166 country codes for geographic identification

### Feature Purpose

KeySTREAM orders certificate products from CAPS (Certificate Authority Provisioning System) for DLMS-compliant smart meters.

**Three Product Types:**

- **MICA** (Meter Identification and Certification Authority) - Root identity for manufacturer
- **DAC** (Device Authentication Certificate) - Individual device certificates (children of MICA)
- **QD Signature** (Qualification Declaration) - Signed qualification documents

**Purpose:**

- Enable certificate provisioning for DLMS smart metering devices
- Support hierarchical certificate structure (MICA → DAC)
- Provide asynchronous order processing with status tracking
- Deliver certificates securely via encrypted packages

## Order Types

### 1. DLMS MICA Creation

**Purpose:**
MICA (Meter Identification and Certification Authority) is the root certificate identity for a meter manufacturer. It represents the manufacturer's identity and is used to sign DACs (Device Authentication Certificates).

**Business Need:**

- One MICA per manufacturer/model/type combination
- Must be created BEFORE ordering DACs
- Contains manufacturer attributes (organization, flag ID, model, type)

**Business Flow:**

1. DLMS tenant (manufacturer) requests MICA creation via API
2. Tenant must be DLMS-enabled (validated via ICPS)
3. KOS validates mandatory fields (caProfile, flagId)
4. KOS creates order with status PENDING
5. Order forwarded to CAPS via SQS message
6. CAPS acknowledges order and creates MICA asynchronously
7. OrderStatusProcessingJob polls every 5 minutes for status updates
8. When MICA ready, CAPS reports serial number
9. KOS stores MICA identity in database with status DELIVERED
10. Notification sent to BSS (Business Support System)

### 2. DLMS DAC Creation

**Purpose:**
DAC (Device Authentication Certificate) packages contain individual certificates for smart meter devices. DACs are "children" of a MICA and require the MICA serial number to be created.

**Business Need:**

- Each physical meter needs its own DAC for authentication
- Ordered in batches (e.g., 49 DACs per order)
- Uses system title range to identify devices uniquely
- Delivered as encrypted package to protect private keys

**Business Flow:**

1. Manufacturer requests DAC package creation for a specific MICA
2. KOS validates MICA exists (throws 404 if not found)
3. Validates system title range (min/max UID)
4. Creates DAC order with encryption details (recipient email, passphrase, public key)
5. Order forwarded to CAPS via SQS
6. CAPS creates DAC batch asynchronously
7. OrderStatusProcessingJob polls every 5 minutes
8. When ready, DACs encrypted with recipient public key
9. Encrypted package delivered to recipient email
10. Notification sent to tenant callback URL

### 3. DLMS QD Signature

**Purpose:**
QD (Qualification Declaration) signature provides cryptographic signing of qualification documents required for DLMS compliance.

**Business Need:**

- Qualification declarations must be signed by trusted CA
- A-XDR Base64 encoded format
- Required for meter qualification/certification

**Business Flow:**

1. Tenant submits Base64-encoded qualification declaration
2. KOS validates mandatory fields (caProfile, qualificationDeclaration)
3. Creates QD signature order
4. Order forwarded to CAPS via SQS
5. CAPS signs the QD asynchronously
6. OrderStatusProcessingJob polls every 5 minutes
7. When ready, signed QD returned in callback
8. Callback includes qualificationDeclaration field (only for DELIVERED status)
9. Notification sent to tenant callback URL

## Business Rules & Constraints

### Tenant Validation

- **Rule:** Only DLMS-enabled tenants can create DLMS orders
- **Why:** DLMS orders require special configuration, CA profiles, and callback URLs that are only set up for DLMS-certified tenants. Non-DLMS tenants would not have the infrastructure to receive or process DLMS certificates.
- **Enforced:** `validateDlmsTenant()` method calls ICPS to verify tenant type
- **Code Location:** `DlmsOrderService.java:134-139`
- **Error:** BadRequestException if tenant is not DLMS type

### Certificate Subject Rules

**X.509 Distinguished Name Format:**

**For MICA:**

- CN (Common Name): Always "MICA" (mandatory, auto-set)
- OI (Organization Identifier): FlagID - three uppercase letters (mandatory)
- O (Organization): Manufacturer name (optional)
- OU (Organizational Unit): Manufacturer's unit (optional)
- FI (Family Information): Model (optional, maps to `model` field)
- P (Pseudonym): Type (optional, maps to `type` field)
- C (Country): ISO 3166 country code (optional)
- L (Locality): City/location (optional)
- ST (State): State name (optional)

**For DAC:**

- CN (Common Name): Always "DAC" (mandatory, auto-set)
- OI (Organization Identifier): FlagID (mandatory)
- FI (Family Information): Model (mandatory)
- P (Pseudonym): Type (mandatory)

**Subject DN Example:**

```
CN=MICA,O=Nagravision,OU=CAPS,OI=MMM,FI=Model123,P=TypeA,C=CH,L=Bern
```

### System Title Range

**What is System Title:**
System Title is a unique identifier (UID) for each smart meter device in the DLMS protocol. It's used for device identification and secure communication.

**Format:**

- FlagID (3 bytes in hex) + 10 hexadecimal digits
- Total: 13 hex characters
- Example: `4354544D4D4D0000000010` (MMM = 4D4D4D in hex)

**Why Range Matters:**

- Manufacturers order DACs in batches
- Each DAC in the batch needs a unique system title
- Range defines start (min) and end (max) UIDs for the batch
- Example: min=`...0010`, max=`...0040` = 49 DACs (0x10 to 0x40)

**Business Fields:**

- **systemTitleMin:** Start of the UID range (FlagID + 10 hex digits)
- **systemTitleMax:** End of the UID range (FlagID + 10 hex digits)

**Constraints:**

- Min must be less than Max
- Both must start with the same FlagID
- Range determines the number of DACs created
- Must be within allocated FlagID space

## Integration Points

### Upstream Dependencies

1. **ICPS (Identity Certificate Provisioning Service)**
   - Purpose: Validates DLMS tenant status before allowing orders
   - Method: `isDlmsTenant(UUID)`
   - **Business Impact if ICPS is down:**
     - All DLMS order creation will fail with 500 errors
     - Cannot validate if tenant is DLMS-enabled
     - Orders cannot proceed past validation step
     - **Recovery:** Queue requests or reject with retry-later error

2. **CAPS (Certificate Authority Provisioning System)**
   - Purpose: External CA system that creates and signs certificates
   - **CAPS Role:** Asynchronously processes MICA/DAC/QD orders, manages PKI infrastructure, signs certificates, returns status updates
   - Integration: SQS messaging (KOS sends JSON payload via SQS queue)
   - **Business Impact if CAPS fails:**
     - Orders stuck in PENDING status
     - No certificates delivered to customers
     - OrderStatusProcessingJob will continue polling
     - Status eventually may show FAILED
     - **Recovery:** Manual investigation required, may need to resubmit orders

### Downstream Dependencies

1. **AWS SQS**
   - Purpose: Message queue for sending DLMS order requests to CAPS
   - **Queue Usage:** KOS creates JSON payload and sends to CAPS SQS queue; CAPS reads from queue and processes asynchronously
   - **Business Impact of queue failures:**
     - Orders created in KOS but not forwarded to CAPS
     - Status remains PENDING indefinitely
     - No certificate production
     - **Recovery:** May need manual resubmission or queue replay

2. **AWS S3**
   - Purpose: Storage for DLMS order payloads and certificate artifacts
   - **What gets stored:** JSON CAPS requests, order metadata, possibly certificate packages for audit/traceability
   - **Business Impact of storage failure:**
     - Cannot store order payloads for investigation
     - Lost traceability for customer queries
     - May impact certificate delivery if S3 used for package storage
     - **Recovery:** Re-create orders or retrieve from backup

3. **AWS SES (Email Service)**
   - Purpose: Sends DAC package delivery emails to recipients
   - **What emails are sent:**
     - DAC package delivery notification
     - Contains encrypted certificate package
     - Sent when DAC order status becomes DELIVERED
   - **Recipients:**
     - Recipient email specified in DAC order request (`recipientEmail` field)
     - Typically manufacturer's technical contact or operations team
   - **Email content:**
     - Order ID and status
     - Encrypted DAC package (protected by recipient's public key)
     - Instructions for decryption
   - **Source:** keySTREAM@kudelski-iot.com
   - **Reply-To:** noreply@kudelski-iot.com

## Order Status Lifecycle

**All Possible Order Statuses (from CAPS):**

1. **PENDING** → Order created, waiting for CAPS to acknowledge
2. **PROCESSING** → CAPS is building the certificates/signatures
3. **DELIVERED** → Certificates/signatures ready and delivered
4. **FAILED** → Order failed during processing (validation error, CA issue, etc.)

**Status Meanings:**

- **PENDING:** Order submitted to CAPS via SQS, awaiting acknowledgment
- **PROCESSING:** CAPS acknowledged and is creating certificates
- **DELIVERED:**
  - For MICA: Serial number available, certificate created
  - For DAC: Package encrypted and sent via email
  - For QD: Signed QD included in callback payload
- **FAILED:** Order could not be completed (check CAPS logs for reason)

**State Transitions:**

```
PENDING → PROCESSING → DELIVERED ✓ (Success path)
PENDING → PROCESSING → FAILED ✗ (Error path)
PENDING → FAILED ✗ (Early rejection)
```

**Status Checking:**

- OrderStatusProcessingJob runs every 5 minutes
- Polls CAPS for status updates
- On status change: updates database and sends notification

## API Endpoints

### Create MICA Order

- **Method:** POST
- **Path:** `/kos/dm/{dm_uuid}/dlms/mica`
- **Request:** `DlmsMicaRequest`
- **Response:** Order ID (UUID)
- **Business Validation:**
  - Tenant must be DLMS-enabled (validated via ICPS)
  - `caProfile` is mandatory
  - `flagId` is mandatory (3 uppercase letters)
  - FlagID format validation
  - Duplicate check (optional)

### Create Test MICA Order

- **Purpose:** For SIT (System Integration Testing) and internal testing without involving CAPS
- **When/Why Used:**
  - During development/testing phases
  - To test downstream flows without external dependencies
  - To create test data quickly
  - For CI/CD pipeline testing
- **Difference from regular MICA:**
  - Skips CAPS integration completely
  - Directly stores MICA with DELIVERED status
  - Requires `serialNumber` in request
  - No SQS message sent
  - Immediate completion
- **Use Case:** SIT testing, demo environments, development workflows

### Other API Endpoints

- **Get Order by ID:** Not explicitly documented, may not exist
- **List Orders:** Get produced MICA - `GET /kos/dm/{dm_uuid}/dlms/mica?flagId={flagId}` returns list of MICA with status "ready"
- **Update Order Status:** Not available via API (updated via CAPS callback/polling)
- **Cancel Order:** Not documented, likely not supported (orders are asynchronous)
- **Create DAC Order:** `POST /kos/dm/{dm_uuid}/dlms/dacs`
- **Create QD Signature:** `POST /kos/dm/{dm_uuid}/dlms/qd`

## Data Model

### DlmsOrder Entity

**Purpose:** Main order record tracking the lifecycle of any DLMS order (MICA, DAC, or QD)

**Business Meaning:** Represents a customer's request for certificate provisioning, maintains order state, stores request payload for traceability

**Key Fields:**

- `orderId`: Unique identifier (UUID) for the order
- `flagId`: **Assigned manufacturer identifier** - three uppercase letters (e.g., "MMM") identifying the meter manufacturer. Used in certificate subjects and system titles.
- `caProfile`: **Certificate Authority profile** - selects which root CA to use (e.g., "test", "prod", "testecc384", "prodecc384"). Maps to CAPS product name "DLMS <caProfile>".
- `dmUuid`: DLMS tenant identifier (which customer owns this order)
- `orderType`: Type of order - MICA_CREATION | DAC_CREATION | QD_SIGNATURE
- `status`: Current order lifecycle status - PENDING | PROCESSING | DELIVERED | FAILED
- `capsRequest`: **Complete JSON payload sent to CAPS** - stored for traceability, customer queries, and debugging. Contains all request parameters.

### DlmsMicaIdentity Entity

**Purpose:** Stores the identity attributes and certificate details for a created MICA

**Business Meaning:** Represents a manufacturer's root certificate identity. One MICA per manufacturer/model/type combination. Contains all X.509 certificate subject attributes.

**Relationship:** One-to-one with DlmsOrder (ORDER_ID is both Primary Key and Foreign Key via @MapsId). Each MICA order has exactly one MICA identity record.

### DlmsDac Entity

**Purpose:** Stores the attributes for a DAC package order

**Business Meaning:** Represents a batch order for device authentication certificates. Contains the range of system titles (device UIDs), MICA reference, and encryption details for secure delivery. Multiple DACs created per order based on system title range.

### DlmsQdSignature Entity

**Purpose:** Stores qualification declaration signature order details

**Business Meaning:** Represents a request to sign a qualification document for DLMS meter certification. Contains the QD payload that needs CA signature.

## Error Handling

### Validation Errors

**Business Error Scenarios:**

1. **Non-DLMS tenant attempts order** → BadRequestException: "Tenant is not a DLMS tenant"
2. **Missing mandatory field (caProfile)** → BadRequestException: "caProfile is required"
3. **Missing mandatory field (flagId)** → BadRequestException: "flagId is required"
4. **Invalid FlagID format** → BadRequestException: "flagId must be 3 uppercase letters"
5. **DAC order with non-existent MICA** → NotFoundException (404): "No MICA found for this flagId/serialNumber"
6. **Invalid system title range** → BadRequestException: "systemTitleMax must be greater than systemTitleMin"
7. **Missing recipient details for DAC** → BadRequestException: "recipientEmail, recipientPassphrase, and recipientPublicKey are required"

### Processing Errors

**What can go wrong during processing:**

1. **CAPS unavailable** - SQS cannot deliver message
2. **S3 storage failure** - Cannot store order payload
3. **Email sending failure** - SES quota exceeded or recipient email invalid
4. **CAPS processing failure** - CAPS returns FAILED status (CA issues, invalid parameters)
5. **Callback URL unreachable** - Cannot notify tenant of status changes
6. **Database failure** - Cannot save order or update status
7. **ICPS unavailable** - Cannot validate tenant during order creation
8. **Invalid encryption key** - Recipient public key format invalid

**Recovery Strategies:**

- **CAPS timeout:** OrderStatusProcessingJob continues polling; eventual manual intervention may be needed
- **Email failure:** No automatic retry; user must contact support
- **Status stuck in PENDING:** Indicates SQS or CAPS issue; check queues and CAPS logs
- **FAILED status:** Check CAPS logs for root cause; may need to recreate order with corrected parameters
- **Transient errors:** Some errors (DB, network) may resolve on next poll cycle

## Qualification Declaration

**What is it:**
Qualification Declaration (QD) is a formal document in A-XDR (Abstract Syntax Notation) format that declares a smart meter's compliance with DLMS specifications and quality standards.

**Purpose:**

- Certifies that a meter meets DLMS/COSEM requirements
- Required for meter qualification and regulatory approval
- Must be cryptographically signed by trusted CA for authenticity
- Part of meter certification process

**Usage:**

- Manufacturer creates QD document in A-XDR format
- Base64-encodes the document
- Submits to KOS for CA signature
- Receives signed QD in callback when DELIVERED
- Signed QD used for meter approval and deployment

## Security Considerations

### Encryption

**Encryption Requirements:**

For DAC package delivery, all private keys and sensitive data must be encrypted:

**Recipient Public Key:**

- Purpose: Used by CAPS to encrypt the DAC package before delivery
- Format: Base64-encoded public key signed by DLMS portal
- Usage: Ensures only the recipient can decrypt the package
- Verification: Key must be signed by trusted DLMS portal

**Passphrase:**

- Purpose: Protects the DAC private keys within the package
- Encryption: Passphrase itself is encrypted with KUD (Kudelski) public key
- Format: Base64-encoded encrypted passphrase
- Security: Double encryption (passphrase encrypts keys, KUD key encrypts passphrase)

### Access Control

**Who can create DLMS orders:**

**Permission Requirements:**

- Must be a DLMS-enabled tenant (validated via ICPS)
- Requires valid DM_UUID (tenant identifier)
- User must have API access credentials
- Tenant must have configured callback URL (for status notifications)
- Tenant must have allocated FlagID

**Tenant Isolation:**

- Each tenant can only access their own orders (filtered by dm_uuid)
- Cross-tenant access prevented by dm_uuid validation
- FlagIDs are unique per tenant/manufacturer

## Monitoring & Notifications

### Order State Change Notifications

- **Event:** DLMS_ORDER_STATE_CHANGED
- **Recipients:**
  - For MICA: BSS (Business Support System)
  - For DAC/QD: Tenant callback URL (configured per tenant by platform admin)
- **Purpose:**
  - Keep external systems in sync with order status
  - Enable automated workflows based on certificate delivery
  - Provide real-time updates to customers
  - Allow BSS to track order fulfillment
- **Triggered by:** OrderStatusProcessingJob detecting status change every 5 minutes

### Email Notifications

- **When:** DAC package is ready (status = DELIVERED)
- **Recipients:**
  - Email address specified in `recipientEmail` field of DAC order
  - Typically manufacturer's technical team or operations
- **Content:**
  - Order ID and status
  - Encrypted DAC package attachment
  - Number of DACs in package
  - Decryption instructions
  - System title range covered
- **From:** keySTREAM@kudelski-iot.com
- **Reply-To:** noreply@kudelski-iot.com

## Testing

### Test MICA Orders

**Purpose:** Allow SIT (System Integration Testing) without CAPS dependency

**How:** Bypasses CAPS integration, directly stores MICA with DELIVERED status. Requires serialNumber in request.

**Use Cases:**

- Integration testing of DAC creation flow (needs existing MICA)
- Demo environments where CAPS is not available
- Development/QA testing without external dependencies
- CI/CD pipeline testing
- Training environments
- Quick test data generation

## Questions Answered

### 1. What business problem does DLMS solve?

DLMS enables secure certificate-based authentication for smart metering devices in the energy/utility sector. It solves the problem of securely identifying and authenticating millions of smart meters communicating with utility head-end systems.

### 2. What is the relationship between MICA and DAC?

MICA (Meter Identification and Certification Authority) is the manufacturer's root identity certificate. DACs (Device Authentication Certificates) are child certificates signed by the MICA. Relationship: One MICA → Many DACs. You must create a MICA first before ordering DACs.

### 3. What is system title and why does it have a range?

System Title is a unique device identifier (UID) in DLMS protocol, formatted as FlagID (3 bytes hex) + 10 hex digits. It has a range because DACs are ordered in batches - each DAC in the batch needs a unique system title. The range (min to max) defines how many DACs are created in the order.

### 4. What is qualification declaration?

Qualification Declaration (QD) is an A-XDR encoded document that certifies a smart meter meets DLMS/COSEM compliance standards. It must be cryptographically signed by a trusted CA and is required for meter regulatory approval and deployment.

### 5. When/why would an order fail?

Orders fail due to: invalid parameters (bad FlagID, missing fields), MICA not found (for DAC orders), CAPS processing errors (CA issues), invalid encryption keys, system title range errors, or infrastructure failures (SQS, S3, CAPS unavailable).

### 6. What is the typical processing time for an order?

Processing is asynchronous: MICA orders typically complete in minutes to hours; DAC packages may take longer depending on batch size; QD signatures are usually quick. Status polling happens every 5 minutes via OrderStatusProcessingJob.

### 7. Are there any volume/rate limits?

Not explicitly documented in the API specs. Limits likely exist at: CAPS processing capacity, SQS throughput, system title range size (affects DAC batch size), AWS SES sending limits for DAC delivery emails.

### 8. What is flagId used for?

FlagID is a manufacturer identifier (3 uppercase letters) assigned to meter manufacturers. Used in: certificate subject (OI field), system title prefix, identifying which MICA to use for DACs, tenant/manufacturer isolation.

### 9. What is CA Profile and how is it configured?

CA Profile selects which root Certificate Authority to use for signing. Examples: "test", "prod", "testecc384", "prodecc384". Configured per tenant, maps to CAPS product name "DLMS <caProfile>". Determines trust chain for certificates.

### 10. Who are the typical users of this feature?

Smart meter manufacturers, utility companies' technical teams, meter certification labs, IoT device provisioning systems, and integration partners who need to provision certificates for DLMS-compliant smart meters.

## Code Locations

### Core Files

- **Service:** `com.nagra.iot.kos.service.DlmsOrderService`
- **DAOs:**
  - `DlmsOrderDao`
  - `DlmsMicaIdentityDao`
  - `DlmsDacDao`
  - `DlmsQdSignatureDao`
- **Entities:** `com.nagra.iot.kos.db.entities.*`
- **API Models:** `com.nagra.iot.kos.json.*`

### Related Components

- **Utilities:** `SendNotification`, `KOSUtils`
- **Client:** `IcpsClient`
- **Tests:** `OrderStatusProcessingJobTest`

---

## Documentation Status

**Last Updated:** Based on Confluence documentation as of April 29, 2026

**Sources:**

- https://nagra-dtv.atlassian.net/wiki/spaces/KSIOT/pages/1962213396/keyStream+DLMS
- Code: `com.nagra.iot.kos.service.DlmsOrderService`
- Database: DLMS_ORDERS, DLMS_MICA_IDENTITY, DLMS_DAC, DLMS_QD_SIGNATURE tables
