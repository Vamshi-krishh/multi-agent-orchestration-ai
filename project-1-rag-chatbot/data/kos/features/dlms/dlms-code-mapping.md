# DLMS Orders - Code Mapping

This document maps business concepts from `dlms-orders.md` to actual code implementation.

## Business Flow → Code Mapping

### MICA Creation Flow

| Business Step | Code Location | Method/Class |
|--------------|---------------|--------------|
| 1. Validate DLMS tenant | `DlmsOrderService.java:134-139` | `validateDlmsTenant(UUID)` |
| 2. Check tenant via ICPS | `IcpsClient.java` | `isDlmsTenant(UUID)` |
| 3. Create order | `DlmsOrderService.java:155-197` | `createDlmsMicaOrderInternal()` |
| 4. Build X.500 subject | `DlmsOrderService.java` | `toSubject()` |
| 5. Create CAPS request | `DlmsOrderService.java` | `createDlmsCapsRequest()` |
| 6. Save to database | `DlmsOrderDao.java` | `create()` |
| 7. Send to SQS | `KOSUtils.java:262` | `sendDlmsToSqs()` |
| 8. Send notification | `SendNotification.java:85` | `sendDlmsOrderStatusNotification()` |

## API Endpoints → Controllers

| Business Function | HTTP Endpoint | Controller Method | Service Method |
|------------------|---------------|-------------------|----------------|
| Create MICA Order | POST /dlms/mica | DlmsOrderResource | `createDlmsMicaOrder()` |
| Create Test MICA | POST /dlms/test-mica | DlmsOrderResource | `createDlmsTestMicaOrder()` |
| Create DAC Order | POST /dlms/dacs | DlmsOrderResource | `createDlmsDacsOrder()` |
| Create QD Signature | POST /dlms/qd | DlmsOrderResource | `createDlmsQdSignatureOrder()` |

## Business Rules → Code Enforcement

| Business Rule | Where Enforced | Code |
|--------------|----------------|------|
| DLMS tenant only | `DlmsOrderService:134` | `if (!icpsClient.isDlmsTenant(dmUuid)) throw BadRequestException` |
| MICA CN = "MICA" | `DlmsOrderService:73` | `MICA_CN` constant |
| DAC CN = "DAC" | `DlmsOrderService:74` | `DAC_CN` constant |
| DAC requires MICA | `DlmsOrderService` | `validateDlmsDacsRequest()` checks MICA exists |
| System title min < max | `DlmsOrderService` | Validation in `validateDlmsDacsRequest()` |

## Data Model → Database Tables

| Entity | Table Name | Purpose |
|--------|-----------|---------|
| `DlmsOrder` | dlms_order | Main order record |
| `DlmsMicaIdentity` | dlms_mica_identity | MICA certificate details |
| `DlmsDac` | dlms_dac | DAC certificate details |
| `DlmsQdSignature` | dlms_qd_signature | QD signature details |

## Integration Points → Code

| External System | Integration Method | Code Location |
|----------------|-------------------|---------------|
| ICPS | REST Client | `IcpsClient.java` |
| CAPS | SQS Message | `KOSUtils.sendDlmsToSqs()` |
| Notification System | Event Notification | `SendNotification.sendDlmsOrderStatusNotification()` |
| AWS S3 | Direct SDK | `AwsS3Operation` |
| AWS SES | Direct SDK | `AwsEmailService` |

## Request/Response Models

| Business Concept | Java Model | Fields |
|-----------------|------------|---------|
| MICA Order Request | `DlmsMicaRequest` | caProfile, flagId, organization, organizationalUnit, model, type, country, locality, state |
| Test MICA Request | `DlmsTestMicaRequest` | extends DlmsMicaRequest + serialNumber |
| DAC Request | `DlmsDacsRequest` | micaSerialNumber, systemTitleMin, systemTitleMax, recipientEmail, recipientPassphrase, recipientPublicKey |
| QD Request | `DlmsQdRequest` | caProfile, qualificationDeclaration (Base64 A-XDR) |

## Order Status → Enum Values

| Business Status | Code Enum | Value |
|----------------|-----------|-------|
| Pending | `OrderStatus.PENDING` | "PENDING" |
| Processing | `OrderStatus.PROCESSING` | "PROCESSING" |
| Delivered | `OrderStatus.DELIVERED` | "DELIVERED" |
| Failed | `OrderStatus.FAILED` | "FAILED" |

## Order Types → Enum Values

| Business Type | Code Enum | Label |
|--------------|-----------|-------|
| MICA Creation | `DlmsOrderType.DLMS_MICA_CREATION` | "DlmsMICACreation" |
| DAC Creation | `DlmsOrderType.DLMS_DAC_CREATION` | "DlmsDACCreation" |
| QD Signature | `DlmsOrderType.DLMS_QD_SIGNATURE` | "DlmsQDSignature" |

## Configuration → Application Config

| Business Setting | Config Path | Default/Example |
|-----------------|-------------|-----------------|
| Qualification CA | `dlmsConfiguration.qualificationCA` | configured per environment |
| SQS URL | `awsConfig.sqsConfiguration` | configured per environment |
| Source Email | Hardcoded | `keySTREAM@kudelski-iot.com` |
| Reply-To Email | Hardcoded | `noreply@kudelski-iot.com` |

## Testing → Test Classes

| Business Scenario | Test Class | Test Method |
|------------------|------------|-------------|
| Order Status Processing | `OrderStatusProcessingJobTest` | Various test methods |

## Constants → Code Constants

| Business Concept | Constant Name | Value |
|-----------------|---------------|-------|
| MICA Common Name | `MICA_CN` | "MICA" |
| DAC Common Name | `DAC_CN` | "DAC" |
| System Title Max Field | `SYSTEM_TITLE_MAX_FIELD_NAME` | "systemTitleMax" |
| System Title Min Field | `SYSTEM_TITLE_MIN_FIELD_NAME` | "systemTitleMin" |
| Subject Field | `ADDITIONAL_FIELD_SUBJECT_NAME` | "subject" |
| CA Profile Field | `ADDITIONAL_FIELD_CA_PROFILE` | "caProfile" |
| Qualification Declaration | `ADDITIONAL_FIELD_QUALIFICATION_DECLARATION` | "qualificationDeclaration" |
| Recipient Email | `ADDITIONAL_FIELD_RECIPIENT_EMAIL` | "recipientEmail" |
| Recipient Passphrase | `ADDITIONAL_FIELD_RECIPIENT_PASSPHRASE` | "recipientPassphrase" |
| Recipient Public Key | `ADDITIONAL_FIELD_RECIPIENT_PUBLIC_KEY` | "recipientPublicKey" |

## Key Dependencies (Maven)

| Dependency | Purpose in DLMS |
|-----------|-----------------|
| BouncyCastle | X.500 certificate subject handling |
| Jackson | JSON serialization for CAPS requests |
| AWS SDK | S3, SES, SQS integration |
| iot-common | Shared models and utilities |

## Search Keywords for RAG

When answering questions about DLMS, search for these keywords in combination:
- dlms, mica, dac, qualification, qd
- order, creation, provisioning
- certificate, x500, subject
- tenant, caps, icps
- systemTitle, caProfile, flagId
