# G & C Brews — CMS

A lightweight Python/Flask CMS to manage your café website content.

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the CMS
python app.py

# 3. Open in browser
http://localhost:5000
```

## What you can manage

| Section        | What it does                                      |
|---------------|---------------------------------------------------|
| **Menu Items** | Add, edit, delete dishes with photos & prices     |
| **Gallery**    | Upload/delete photos shown on the website         |
| **Hours**      | Update Mon–Fri, Saturday, Sunday opening times    |
| **Hero Text**  | Edit the homepage tagline and description         |
| **Contact**    | Update address, Instagram handle, phone number    |

## How it connects to your website

The CMS saves everything to `data/site_data.json`.
Your website can read this file directly, or fetch it via:

```
GET http://localhost:5000/api/site-data
```

Returns JSON with all content — hours, menu, gallery, contact info.

## File structure

```
gnc-cms/
├── app.py                  # Main Flask app
├── requirements.txt
├── data/
│   └── site_data.json      # All your content lives here
├── static/
│   └── uploads/            # Uploaded photos stored here
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── menu.html
    ├── menu_form.html
    ├── gallery.html
    ├── hours.html
    ├── hero.html
    └── contact.html
```
