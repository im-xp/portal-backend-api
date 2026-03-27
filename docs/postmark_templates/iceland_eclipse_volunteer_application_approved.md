# Iceland Eclipse Volunteer Approval Email

Suggested Postmark template alias: `iceland-volunteer-invitation`

This template is intended to be mapped to the `application-approved` event for the Iceland volunteer popup. The review endpoint now accepts an optional `review_email` payload and stores it under `application.custom_data.review_email`, which is then exposed to Postmark as template model data.

## Suggested Subject

```txt
Your Iceland Eclipse Volunteer Invitation
```

## Text Body

```txt
Hello {{first_name}},

We’re delighted to welcome you into the Iceland Eclipse Volunteer Program and the team helping bring this gathering to life! To secure your place with the crew, please complete the steps below. Your participation will only be confirmed once these steps are completed.

{{#has_single_approved_phase}}
We're excited to confirm your placement in the {{single_phase.name}}.

Arrival: {{single_phase.arrival_date}}
Work: {{single_phase.work_requirement}}
Accommodation: {{single_phase.accommodation}}
Meals: {{single_phase.meals}}
Travel: Roundtrip shuttle from KEF

IMPORTANT: Your mandatory arrival date is {{single_phase.arrival_date}}. If you are unable to arrive to Reykjavik by {{single_phase.latest_arrival_date}}, please reply to this email so we can work to reassign you to a different phase, space permitting.
{{/has_single_approved_phase}}
{{#has_multiple_approved_phases}}
You've been approved for the following phase(s): {{approved_phase_names}}

Please review each option carefully and select the one you'd like to commit to when you fill out the Confirmation Form below.
{{/has_multiple_approved_phases}}

Confirm Your Participation

{{#requires_refundable_deposit}}
To confirm your participation, you’ll need to pay the ${{deposit_amount}} refundable deposit. The deposit will be refunded once you complete your work requirement. Payment plans are available during the checkout process.
{{/requires_refundable_deposit}}
{{#deposit_waived}}
The Volunteer Coordinator has opted to waive your ${{deposit_amount}} refundable deposit. Please confirm your participation via the form link below.
{{/deposit_waived}}
{{#ticket_holder_credit}}
Since you’ve already purchased a ticket, you do not need to pay the ${{deposit_amount}} refundable deposit. Instead, your order will be refunded ${{deposit_amount}} upon completion of the work requirement. Please confirm your participation via the form link below.
{{/ticket_holder_credit}}

Confirmation Form: {{confirmation_form_link}}

What Next?

Team Assignments: Once the program has filled (expected sometime in July), we'll assign everyone to their teams. From there, you'll be able to request specific shifts within your phase.

Arrival Logistics: We'll send you a detailed arrival email in mid-July covering all on-site logistics: where to go, what to bring, shuttle timing, and everything else you need to arrive prepared.

In the meantime, don't hesitate to reach out if you have any questions.

Thank you for bringing your time and energy to this special gathering.

See you in Iceland,
The Iceland Eclipse Team
```

## Full HTML Template

```html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <title>Your Iceland Eclipse Volunteer Invitation</title>
  <style type="text/css">
    body {
      margin: 0;
      padding: 0;
      background-color: #f4f7fb;
      color: #17324d;
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.6;
    }
    table {
      border-collapse: collapse;
    }
    .email-wrap {
      width: 100%;
      background-color: #f4f7fb;
      padding: 24px 0;
    }
    .email-card {
      width: 100%;
      max-width: 640px;
      margin: 0 auto;
      background-color: #ffffff;
      border: 1px solid #d8e2ee;
    }
    .email-inner {
      padding: 40px 32px;
    }
    .eyebrow {
      font-size: 12px;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      color: #5c7894;
      margin: 0 0 16px;
    }
    h1 {
      font-size: 28px;
      line-height: 1.25;
      margin: 0 0 24px;
      color: #0f2740;
    }
    h2 {
      font-size: 20px;
      line-height: 1.3;
      margin: 32px 0 16px;
      color: #0f2740;
    }
    p {
      margin: 0 0 16px;
      font-size: 16px;
    }
    ul {
      margin: 0 0 16px 20px;
      padding: 0;
    }
    li {
      margin: 0 0 8px;
      font-size: 16px;
    }
    .notice {
      padding: 16px;
      background-color: #fff4df;
      border-left: 4px solid #f2a93b;
      margin: 20px 0;
    }
    .cta {
      margin: 24px 0 28px;
    }
    .cta a {
      display: inline-block;
      background-color: #0f5d7a;
      color: #ffffff;
      text-decoration: none;
      padding: 14px 22px;
      font-weight: bold;
    }
    .divider {
      border-top: 1px solid #d8e2ee;
      margin: 32px 0;
    }
    .footer {
      color: #5c7894;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <table role="presentation" class="email-wrap" width="100%">
    <tr>
      <td align="center">
        <table role="presentation" class="email-card" width="100%">
          <tr>
            <td class="email-inner">
              <p class="eyebrow">Iceland Eclipse Volunteer Program</p>
              <h1>Your invitation is ready</h1>

              <p>Hello {{first_name}},</p>

              <p>We’re delighted to welcome you into the Iceland Eclipse Volunteer Program and the team helping bring this gathering to life. To secure your place with the crew, please complete the steps below. Your participation will only be confirmed once these steps are completed.</p>

              {{#has_single_approved_phase}}
              <h2>Invitation</h2>
              <p>We're excited to confirm your placement in the <strong>{{single_phase.name}}</strong>.</p>
              <ul>
                <li><strong>Arrival:</strong> {{single_phase.arrival_date}}</li>
                <li><strong>Work:</strong> {{single_phase.work_requirement}}</li>
                <li><strong>Accommodation:</strong> {{single_phase.accommodation}}</li>
                <li><strong>Meals:</strong> {{single_phase.meals}}</li>
                <li><strong>Travel:</strong> Roundtrip shuttle from KEF</li>
              </ul>
              <div class="notice">
                <p><strong>Important:</strong> Your mandatory arrival date is {{single_phase.arrival_date}}. If you are unable to arrive to Reykjavik by {{single_phase.latest_arrival_date}}, please reply to this email so we can work to reassign you to a different phase, space permitting.</p>
              </div>
              {{/has_single_approved_phase}}

              {{#has_multiple_approved_phases}}
              <h2>Invitation</h2>
              <p>You've been approved for the following phase(s): <strong>{{approved_phase_names}}</strong></p>
              <p>Please review each option carefully and select the one you'd like to commit to when you fill out the Confirmation Form below.</p>
              {{/has_multiple_approved_phases}}

              <h2>Confirm Your Participation</h2>

              {{#requires_refundable_deposit}}
              <p>To confirm your participation, you’ll need to pay the ${{deposit_amount}} refundable deposit. The deposit will be refunded once you complete your work requirement. Payment plans are available during the checkout process.</p>
              {{/requires_refundable_deposit}}

              {{#deposit_waived}}
              <p>The Volunteer Coordinator has opted to waive your ${{deposit_amount}} refundable deposit. Please confirm your participation via the form link below.</p>
              {{/deposit_waived}}

              {{#ticket_holder_credit}}
              <p>Since you’ve already purchased a ticket, you do not need to pay the ${{deposit_amount}} refundable deposit. Instead, your order will be refunded ${{deposit_amount}} upon completion of the work requirement. Please confirm your participation via the form link below.</p>
              {{/ticket_holder_credit}}

              <div class="cta">
                <a href="{{confirmation_form_link}}">Open Confirmation Form</a>
              </div>

              <div class="divider"></div>

              <h2>What Next?</h2>
              <p><strong>Team Assignments:</strong> Once the program has filled, expected sometime in July, we'll assign everyone to their teams. From there, you'll be able to request specific shifts within your phase.</p>
              <p><strong>Arrival Logistics:</strong> We'll send you a detailed arrival email in mid-July covering all on-site logistics: where to go, what to bring, shuttle timing, and everything else you need to arrive prepared.</p>
              <p>In the meantime, don't hesitate to reach out if you have any questions.</p>
              <p>Thank you for bringing your time and energy to this special gathering.</p>

              <p class="footer">See you in Iceland,<br />The Iceland Eclipse Team</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

## Example Review Request Payload

```json
{
  "status": "accepted",
  "discount_assigned": 0,
  "review_email": {
    "confirmation_form_link": "https://example.com/iceland/confirm",
    "deposit_mode": "waived",
    "deposit_amount": 600,
    "approved_phases": [
      {
        "name": "Build Week",
        "arrival_date": "August 1, 2026",
        "work_requirement": "4 shifts",
        "accommodation": "Shared volunteer housing",
        "meals": "Breakfast and dinner",
        "latest_arrival_date": "July 31, 2026"
      },
      {
        "name": "Event Week",
        "arrival_date": "August 8, 2026",
        "work_requirement": "3 shifts",
        "accommodation": "Shared volunteer housing",
        "meals": "Breakfast and dinner",
        "latest_arrival_date": "August 7, 2026"
      }
    ]
  }
}
```
