# /tickets API Endpoint Documentation

### What is this endpoint for?
This endpoint is used to retrieve tickets associated with a specific attendee's email.

### How should I use it?
To use this endpoint, you need to send a GET request with the following:

- **Query Parameter:**
  - `email` (string, required): The email of the attendee whose tickets you want to retrieve.

- **Header:**
  - `X-API-Key` (string, required): Your API key for authentication.

### How can I get an API KEY?
To obtain an API key, please send an email to [mateo@simplefi.tech](mailto:mateo@simplefi.tech) with your request.

### What is the response format?
The response will be a list of attendees with their associated tickets. Here is an example:

```json
[
  {
    "name": "Alex Smith",
    "email": "alex.smith@example.com",
    "category": "main",
    "popup_city": "Edge Esmeralda 2025",
    "products": [
      {
        "name": "Month",
        "category": "month",
        "start_date": "2025-05-24T18:00:00",
        "end_date": "2025-06-21T18:00:00"
      }
    ]
  },
  {
    "name": "Alex Smith",
    "email": "alex.smith@example.com",
    "category": "main",
    "popup_city": "Edge Bhutan 2025",
    "products": []
  },
  {
    "name": "Alex Smith",
    "email": "alex.smith@example.com",
    "category": "main",
    "popup_city": "Edge Expedition South Africa",
    "products": []
  },
  {
    "name": "Alex Smith",
    "email": "alex.smith@example.com",
    "category": "main",
    "popup_city": "Edge Patagonia",
    "products": []
  }
]
```

---

**← [Back to Documentation Index](./index.md)**
