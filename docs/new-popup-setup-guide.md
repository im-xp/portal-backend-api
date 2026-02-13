# Plan: Setting Up a Volunteers Popup in EdgeOS

## Summary

EdgeOS supports multi-tenant "popups" through a combination of: (1) a database record defining the popup, its products, and email templates, (2) frontend configuration files for forms, branding, routing, and metadata, and (3) Vercel + DNS setup for the subdomain. Ripple on the Nile is the reference implementation. This plan provides step-by-step instructions for replicating that setup for a "Volunteers" popup.

**Reality check:** About half these steps require editing code files and running scripts. A non-technical partner can prepare the *content* (questions, branding choices, product definitions), but the code changes and deployment need a developer. The plan is structured to clearly separate those responsibilities.

---

## Research

### How Ripple Works (Architecture)

The Ripple popup touches **7 files** across two repos plus infrastructure:

| Layer | File | Purpose |
|-------|------|---------|
| **Backend** | `EdgeOS_API/scripts/ripple_popup_city.json` | Popup metadata (name, slug, dates, flags) |
| **Backend** | `EdgeOS_API/scripts/ripple_products.csv` | Ticket/pass types with prices |
| **Backend** | `EdgeOS_API/scripts/ripple_email_templates.csv` | Transactional email mappings |
| **Frontend** | `EdgeOS/src/constants/Forms/ripple-on-the-nile.ts` | Application form questions |
| **Frontend** | `EdgeOS/src/constants/popupBranding.ts` | Colors, logo, hero image, name |
| **Frontend** | `EdgeOS/src/constants/index.ts` | Form registry (slug -> form config) |
| **Frontend** | `EdgeOS/src/middleware.ts` | Domain -> slug cookie mapping |
| **Frontend** | `EdgeOS/src/app/layout.tsx` | SEO metadata per domain |
| **Frontend** | `EdgeOS/vercel.json` | URL rewrites for subdomain routing |
| **Infra** | Vercel Dashboard | Custom domain attachment |
| **Infra** | DNS Provider | CNAME record for subdomain |
| **Payments** | SimpleFi | API key for payment processing (optional) |

### Routing Flow

```
volunteers.example.com
  -> DNS CNAME -> Vercel
  -> vercel.json rewrites add ?popup=volunteers-portal
  -> middleware.ts sets popup_slug cookie
  -> usePopupSlug() reads cookie or query param
  -> getPopupBranding() applies theme
  -> dynamicForm['volunteers-portal'] loads form questions
```

---

## Step-by-Step Instructions

### Prerequisites (BLOCKING - Must Complete Before Starting)

Before any developer work begins, these must be ready:

1. **Image assets uploaded to cloud storage** (logo, hero image, background, OG image). Placeholder URLs will break the branding. Partner must provide final hosted URLs.
2. **Email templates created in your email service.** The CSV references template names. If those templates don't exist, users will sign up and receive no confirmation email. Silent failure = confused users.
3. **Decision: `requires_approval`?** For paid popups (Ripple), approval gates portal access. For free volunteers, consider whether you actually need approval. If every volunteer should get immediate access, set this to `false`. If you want to vet volunteers first, keep `true` and designate who reviews applications.

---

### Phase 1: Content Preparation (Non-Technical Partner)

These steps don't require code. Gather this info and send it to your developer.

#### Step 1.1: Choose a Slug and Name

Pick a URL-friendly slug and display name:

- **Display name**: e.g., "Eclipse Volunteers"
- **Slug**: e.g., `eclipse-volunteers` (lowercase, hyphens, no spaces)
- **Subdomain**: e.g., `volunteers.egypt-eclipse.com`
- **Contact email**: e.g., `volunteers@egypt-eclipse.com`

#### Step 1.2: Define Your Application Form Questions

Look at Ripple's form for reference. It has three sections with standard fields plus custom questions.

**Standard fields you can include** (these map to existing database columns):
- `first_name`, `last_name`, `email`, `telegram`
- `social_media` (website/social links)
- `organization`, `role`

**Custom fields** (stored as JSON, you define the questions):

For each custom question, decide:
- **Label**: The question text
- **Type**: `text` (short answer), `textarea` (long answer), `boolean` (yes/no), `select` (dropdown)
- **Section**: Which form section it belongs to (`personal_information`, `professional_details`, or `participation`)
- **Required**: Yes or no
- **Placeholder**: Helper text shown in empty field

Example for volunteers:
```
Section: "About You"
1. "What skills or expertise can you contribute?" (textarea, required)
2. "How many hours per week are you available?" (text, required)
3. "What type of volunteer work interests you most?" (textarea, required)
4. "Have you volunteered at similar events before?" (textarea, optional)
```

#### Step 1.3: Define Products/Passes

If volunteers need to "register" or select tracks, define them. For a free volunteer signup, this can be simple:

| Name | Slug | Price | Description |
|------|------|-------|-------------|
| Volunteer Registration | volunteer-registration | 0 | Standard volunteer registration |

If you have different volunteer tracks or tiers, add more rows.

#### Step 1.4: Prepare and Upload Image Assets (BLOCKING)

These must be **uploaded and hosted** before dev work starts. Dev needs real URLs, not "we'll get to it later."

Provide your developer with **hosted URLs** for:
- **Logo** (square, ~400x400px PNG with transparency)
- **Hero image** (rectangular, ~1200x630px)
- **Background image** (large, ~1920x1080)
- **OG/social share image** (1200x630px, for link previews)

Upload to Google Cloud Storage, Cloudflare R2, or wherever your other assets live (Ripple uses `storage.googleapis.com/egypt-eclipse/`).

#### Step 1.5: Choose Branding Colors

Provide your developer with:
- **Welcome message**: Optional greeting text
- **Color scheme**: Primary and secondary colors (hex codes are fine, dev will convert to HSL)
  - Background color
  - Text color
  - Accent/button color

#### Step 1.6: Define Email Templates

Decide which automated emails you need. Ripple uses these events:
- `application-received` - Sent when someone applies
- `application-approved` - Sent when admin approves
- `auth-citizen-portal` - Login/auth email
- `payment-confirmed` - Payment receipt

For each, you need a template name (your developer will set these up in whatever email service you use).

---

### Phase 2: Backend Setup (Developer Required)

#### Step 2.1: Create the Popup City JSON

Create `EdgeOS_API/scripts/volunteers_popup_city.json`:

```json
{
    "name": "Eclipse Volunteers",
    "slug": "eclipse-volunteers",
    "prefix": "VOLUNTEERS",
    "tagline": "Join our volunteer team",
    "location": "Global",
    "passes_description": "Register as a volunteer",
    "image_url": "https://storage.googleapis.com/YOUR_BUCKET/volunteers-logo.png",
    "start_date": "2026-03-01T00:00:00",
    "end_date": "2027-08-15T23:59:59",
    "clickable_in_portal": true,
    "visible_in_portal": true,
    "requires_approval": true,
    "allows_spouse": false,
    "allows_children": false,
    "allows_coupons": false,
    "contact_email": "volunteers@egypt-eclipse.com"
}
```

**Notes:**
- `requires_approval: true` means volunteer signups need manual admin approval before they get portal access
- Omit `simplefi_api_key` if there's no payment processing (free registration)
- Adjust dates to your actual volunteer program window

#### Step 2.2: Create the Products CSV

Create `EdgeOS_API/scripts/volunteers_products.csv`:

```csv
name,slug,price,compare_price,description,category,attendee_category,start_date,end_date,is_active,exclusive
Volunteer Registration,volunteer-registration,0.0,,Standard volunteer registration,month,main,2026-03-01 00:00:00,2027-08-15 23:59:59,True,False
```

Add more rows if you have multiple volunteer tracks.

#### Step 2.3: Create the Email Templates CSV

Create `EdgeOS_API/scripts/volunteers_email_templates.csv`:

```csv
event,template,frequency
application-received,volunteers-application-received,
application-approved,volunteers-application-approved,
auth-citizen-portal,volunteers-auth-citizen-portal,
```

**Note:** The `template` values must match template names configured in your email service. Create those templates first or use existing ones.

#### Step 2.4: Run the Setup Script

```bash
cd /path/to/EdgeOS_API

# Dry run first to verify files load correctly
python scripts/add_popup_city.py volunteers --dry-run

# If dry run looks good, run for real
python scripts/add_popup_city.py volunteers
# Type 'y' when prompted
```

**Environment requirements:** The script needs database connectivity. Either:
- Run inside Docker: `docker compose exec api python scripts/add_popup_city.py volunteers`
- Or have `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD` env vars set

**Expected output:**
```
============================================================
Adding popup city from: volunteers_*.json/csv
Database: localhost:5432/edgeos_db
============================================================

Loaded popup config: Eclipse Volunteers
Loaded 1 products
Loaded 3 email templates

This will create:
  - Popup: Eclipse Volunteers (eclipse-volunteers)
  - 1 products
  - 3 email templates

Proceed? (y/N): y
  Created popup city: Eclipse Volunteers (ID: X, order: Y)
  Product: Volunteer Registration
Products: 1 inserted, 0 skipped
  Template: application-received -> volunteers-application-received
  Template: application-approved -> volunteers-application-approved
  Template: auth-citizen-portal -> volunteers-auth-citizen-portal
Email templates: 3 inserted, 0 skipped

Done! Popup city ID: X
```

#### Step 2.5: Verify in NocoDB

Open NocoDB (http://localhost:8080 or your production URL), navigate to the `popups` table, and confirm the new row exists with correct data.

---

### Phase 3: Frontend Setup (Developer Required)

#### Step 3.1: Create Form Configuration

Create `EdgeOS/src/constants/Forms/eclipse-volunteers.ts`:

```typescript
import { DynamicForm } from ".."

export const eclipseVolunteers: DynamicForm = {
  local: 'Global',
  personal_information: {
    title: 'Your Information',
    subtitle: 'Welcome! Tell us about yourself to join the volunteer team.',
  },
  professional_details: {
    title: 'Your Background',
    subtitle: 'Help us understand your experience',
  },
  participation: {
    title: 'Volunteering',
    subtitle: 'How you want to contribute',
  },
  fields: [
    "first_name",
    "last_name",
    "email",
    "telegram",
    "organization",
    "role",
  ],
  customFields: [
    {
      key: "skills",
      label: "What skills or expertise can you contribute?",
      type: "textarea",
      placeholder: "e.g., event planning, social media, translation, tech support",
      section: "professional_details",
      required: true,
    },
    {
      key: "availability",
      label: "How many hours per week are you available?",
      type: "text",
      placeholder: "e.g., 5-10 hours",
      section: "participation",
      required: true,
    },
    {
      key: "interests",
      label: "What type of volunteer work interests you most?",
      type: "textarea",
      placeholder: "e.g., logistics, communications, community building",
      section: "participation",
      required: true,
    },
    {
      key: "prior_experience",
      label: "Have you volunteered at similar events before?",
      type: "textarea",
      placeholder: "Tell us about any relevant experience",
      section: "participation",
      required: false,
    },
  ],
}
```

**Customize the questions based on what the partner provided in Step 1.2.**

#### Step 3.2: Register the Form

Edit `EdgeOS/src/constants/index.ts`:

Add the import at the top:
```typescript
import { eclipseVolunteers } from "./Forms/eclipse-volunteers";
```

Add the entry to the `dynamicForm` record:
```typescript
export const dynamicForm: Record<string, DynamicForm | null> = {
  // ... existing entries ...
  'eclipse-volunteers': eclipseVolunteers,
}
```

#### Step 3.3: Add Branding

Edit `EdgeOS/src/constants/popupBranding.ts`:

Add a new entry to the `popupBranding` record (before the closing `}`):

```typescript
  'eclipse-volunteers': {
    name: 'Eclipse Volunteers',
    logo: 'https://storage.googleapis.com/YOUR_BUCKET/volunteers-logo.png',
    logoAlt: 'Eclipse Volunteers logo',
    heroImage: 'https://storage.googleapis.com/YOUR_BUCKET/volunteers-hero.png',
    heroAlt: 'Eclipse Volunteers hero image',
    backgroundImage: 'https://storage.googleapis.com/YOUR_BUCKET/volunteers-bg.jpg',
    welcomeMessage: 'Welcome to Eclipse Volunteers!',
    colors: {
      // Adjust these HSL values to match desired brand colors
      // Tip: Use https://hslpicker.com to convert hex to HSL
      background: '0 0% 98%',
      foreground: '220 50% 15%',
      primary: '142 60% 45%',           // Green accent
      primaryForeground: '0 0% 100%',
      secondary: '220 50% 15%',
      secondaryForeground: '0 0% 100%',
      muted: '210 20% 93%',
      mutedForeground: '220 30% 35%',
      accent: '142 60% 45%',
      accentForeground: '220 50% 15%',
      border: '210 25% 85%',
      input: '210 25% 90%',
      ring: '142 60% 45%',
      card: '0 0% 100%',
      cardForeground: '220 50% 15%',
      popover: '0 0% 100%',
      popoverForeground: '220 50% 15%',
      sidebarBackground: '220 50% 13%',
      sidebarForeground: '210 8% 90%',
      sidebarPrimary: '142 60% 45%',
      sidebarPrimaryForeground: '0 0% 100%',
      sidebarAccent: '220 45% 18%',
      sidebarAccentForeground: '210 8% 90%',
      sidebarBorder: '220 40% 25%',
      sidebarRing: '142 60% 45%',
    },
  },
```

#### Step 3.4: Add Domain Routing

Edit `EdgeOS/src/middleware.ts` - add the new domain to the map:

```typescript
const domainToPopup: Record<string, string> = {
  'ripple.egypt-eclipse.com': 'ripple-on-the-nile',
  'volunteers.egypt-eclipse.com': 'eclipse-volunteers',  // NEW
}
```

#### Step 3.5: Add SEO Metadata

Edit `EdgeOS/src/app/layout.tsx` - add the new domain to `popupMetadata`:

```typescript
const popupMetadata: Record<string, { ... }> = {
  'ripple.egypt-eclipse.com': { ... },
  'volunteers.egypt-eclipse.com': {                      // NEW
    title: 'Eclipse Volunteers',
    description: 'Join the Eclipse volunteer team. Sign up to contribute your skills and time.',
    image: 'https://storage.googleapis.com/YOUR_BUCKET/volunteers-og.png',
  },
  'default': { ... },
};
```

#### Step 3.6: Add Vercel URL Rewrites

Edit `EdgeOS/vercel.json` - add rewrite rules for the new subdomain:

```json
{
  "rewrites": [
    {
      "source": "/",
      "has": [{ "type": "host", "value": "ripple.egypt-eclipse.com" }],
      "destination": "/?popup=ripple-on-the-nile"
    },
    {
      "source": "/auth",
      "has": [{ "type": "host", "value": "ripple.egypt-eclipse.com" }],
      "destination": "/auth?popup=ripple-on-the-nile"
    },
    {
      "source": "/:path*",
      "has": [{ "type": "host", "value": "ripple.egypt-eclipse.com" }],
      "destination": "/:path*?popup=ripple-on-the-nile"
    },
    {
      "source": "/",
      "has": [{ "type": "host", "value": "volunteers.egypt-eclipse.com" }],
      "destination": "/?popup=eclipse-volunteers"
    },
    {
      "source": "/auth",
      "has": [{ "type": "host", "value": "volunteers.egypt-eclipse.com" }],
      "destination": "/auth?popup=eclipse-volunteers"
    },
    {
      "source": "/:path*",
      "has": [{ "type": "host", "value": "volunteers.egypt-eclipse.com" }],
      "destination": "/:path*?popup=eclipse-volunteers"
    }
  ]
}
```

---

### Phase 4: Infrastructure (Developer Required)

**Order matters here. Do these in sequence, not parallel.**

#### Step 4.1: Deploy Frontend First

Commit and push the frontend changes. Vercel must know about the rewrite rules *before* the domain is pointed.

```bash
cd EdgeOS
git add src/constants/Forms/eclipse-volunteers.ts \
        src/constants/index.ts \
        src/constants/popupBranding.ts \
        src/middleware.ts \
        src/app/layout.tsx \
        vercel.json
git commit -m "Add eclipse-volunteers popup configuration"
git push
```

Wait for Vercel deployment to complete (check Vercel dashboard or GitHub commit status).

#### Step 4.2: Add Domain in Vercel

1. Go to Vercel Dashboard -> your EdgeOS project -> Settings -> Domains
2. Click "Add Domain"
3. Enter: `volunteers.egypt-eclipse.com`
4. Vercel will show you the required DNS record

#### Step 4.3: Add DNS Record (AFTER Vercel domain is added)

In your DNS provider (Cloudflare, Route53, etc.):

1. Add a CNAME record:
   - **Name**: `volunteers`
   - **Target**: `cname.vercel-dns.com` (or whatever Vercel specifies)

2. **Cloudflare users: Set proxy to DNS-only (grey cloud, NOT orange).** Cloudflare proxy + Vercel causes SSL certificate conflicts. Vercel handles its own SSL.

3. Wait for DNS propagation (usually minutes, can take up to 48 hours)

---

### Phase 5: Verification

#### Step 5.1: Test Without Subdomain (Do This First)

Don't wait for DNS. Use the query param approach immediately after frontend deploy:

Visit: `https://your-edgeos-domain.com/?popup=eclipse-volunteers`

Verify:
- [ ] Branding colors apply correctly
- [ ] Logo and images display (no broken images)
- [ ] Application form shows correct sections and questions
- [ ] Form submission works
- [ ] Confirmation email arrives (if email templates are set up)
- [ ] $0 product/checkout flow works correctly (no payment screen for free registration)
- [ ] Admin can see the application in NocoDB

#### Step 5.2: Test With Subdomain (After DNS Propagation)

Visit: `https://volunteers.egypt-eclipse.com`

Verify:
- [ ] Domain resolves (no DNS errors, no Vercel 404)
- [ ] SSL certificate is valid (green lock)
- [ ] Popup loads automatically without `?popup=` in the URL
- [ ] Full signup flow works end-to-end
- [ ] OG metadata shows correctly (paste link in Slack/Twitter to test preview)

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Payment processing | Omit SimpleFi key initially | Volunteers typically register for free. Can add later. |
| `requires_approval` | `true` | Volunteer applications should be reviewed before granting portal access |
| Form structure | 3 sections matching Ripple pattern | Consistent UX across all popups |
| Branding | Light theme with green accent | Differentiate from Iceland (cyan) and Ripple (gold/brown). Partner should specify actual colors. |

## Open Questions

1. **What's the actual subdomain?** `volunteers.egypt-eclipse.com` is a placeholder. Partner needs to confirm.
2. **Do volunteers need payment processing?** If yes, need SimpleFi merchant setup (separate process).
3. **Should volunteers see other popups in the sidebar?** The `visible_in_portal` flag controls whether this shows up for other popup users.
4. **What does the volunteer portal experience look like post-signup?** Ripple users see passes/cabins to purchase. Volunteers with a $0 registration need a sensible post-login experience. This may need separate UX consideration.

## Estimated Complexity

| Phase | Who | Time |
|-------|-----|------|
| Phase 1: Content prep | Non-technical partner | 1-2 hours |
| Phase 2: Backend setup | Developer | 15-30 min |
| Phase 3: Frontend setup | Developer | 30-45 min |
| Phase 4: Infrastructure | Developer | 15-30 min |
| Phase 5: Verification | Both | 15-30 min |
| **Total** | | **~2-3 hours** |

## References

- Ripple form config: `EdgeOS/src/constants/Forms/ripple-on-the-nile.ts`
- Ripple branding: `EdgeOS/src/constants/popupBranding.ts:84-125`
- Ripple popup JSON: `EdgeOS_API/scripts/ripple_popup_city.json`
- Ripple products: `EdgeOS_API/scripts/ripple_products.csv`
- Setup script: `EdgeOS_API/scripts/add_popup_city.py`
- Middleware routing: `EdgeOS/src/middleware.ts`
- Vercel rewrites: `EdgeOS/vercel.json`
- Form registry: `EdgeOS/src/constants/index.ts`
- SEO metadata: `EdgeOS/src/app/layout.tsx:15-32`

## Review Notes

Council of Experts review conducted 2026-02-12.

### Incorporated
- Email template creation moved from "open question" to **blocking prerequisite** (Skeptic: silent email failures)
- Image asset preparation moved into Phase 1 as blocking deliverable (Executor: quiet blocker)
- Explicit deployment ordering: frontend deploy -> Vercel domain -> DNS (Executor: Vercel 404 race condition)
- Cloudflare proxy warning added to DNS step (Executor: SSL conflict gotcha)
- `requires_approval` decision surfaced as prerequisite (Visionary: approval bottleneck for high-volume volunteer signups)
- $0 product checkout verification added to test checklist (Skeptic: untested UX path)
- Query-param testing as primary verification path, don't wait for DNS (Skeptic: DNS as false blocker)

### Deferred
- Post-signup volunteer portal UX (Visionary: valid concern, separate scope, added to Open Questions)
- Auto-approval toggle (Visionary: partner decision, not plan decision)

### Rejected
- None. All feedback was actionable.
