# SJ Capitals – Investment Platform

## 🧱 Tech Stack
- **Backend:** Django
- **Frontend:** Bootstrap, JavaScript, CSS
- **Database:** PostgreSQL

---

## 🎯 Project Overview

SJ Capitals is an investment platform where users can view company details and subscribe to investment plans. The company invests in crypto, forex, and other legitimate (non-gambling/haram) trading avenues. Users can track their investment progress and receive periodic payouts. 

All payouts will be manually created by the **Admin** based on 4–10% of the user’s principal every 10 days.

---

## 🌐 Public Pages

### 1. Landing Page
- Company Introduction
- Investment Philosophy
- Display of Active Plans
- Contact Info & FAQs

### 2. User Authentication
- Register / Login
- Email Verification
- Forgot Password / Reset Flow

---

## 🧑‍💼 Client Dashboard

### a. Subscribed Plans
- Plan Name
- Subscribed Amount
- Start Date
- End Date (based on plan duration)
- Remaining Days
- Status: Active / Completed

### b. Investment Allocation
- Categories: e.g., Crypto, Forex
- Optional % breakdown by type (Admin-defined)

### c. Payout Schedule
- List of scheduled payouts (created manually by Admin)
- Each payout includes:
  - Date
  - Payout % and amount
  - Status: Paid / Pending

---

## 🛠️ Admin Panel Features

- Create/Edit/Delete Investment Plans
- View All Users & Subscriptions
- Manually Create Payouts per Subscription
  - Define payout % (4–10%) and date
- Assign investment type (e.g., Crypto, Forex) to user funds
- Manage payout statuses (Mark as Paid)

---

## 🗃️ Database Schema Overview

### `User` (Django Default)
- `username`, `email`, `password`, etc.

### `Plan`
- `id`
- `name`
- `description`
- `min_invest`, `max_invest`
- `duration_days`

### `Subscription`
- `id`
- `user_id` (FK)
- `plan_id` (FK)
- `amount`
- `start_date`
- `status` (Active / Completed)

### `Payout`
- `id`
- `subscription_id` (FK)
- `date`
- `payout_percent`
- `payout_amount`
- `status` (Pending / Paid)

### `InvestmentAllocation` *(Optional)*
- `id`
- `subscription_id` (FK)
- `market_type` (e.g., Crypto, Forex)
- `percentage`

---

## 🔐 Security
- Enforce HTTPS & CSRF protection
- Sanitize user inputs
- Use Django's built-in auth system
- Restrict Admin-only actions behind `@staff_member_required` decorators

---

## ✅ Example Flow

1. User lands on homepage → views plans
2. Registers and subscribes to a plan
3. Admin sees subscription, defines investment category
4. Admin manually creates a payout (4–10%) every 10 days
5. User sees payout history and upcoming payments in dashboard

---

## 🚀 Future Enhancements
- Auto-email reminders for payouts
- Withdrawal requests and approval system
- Mobile responsiveness and dark mode


## Template Folder Structure

```
templates/
    common/
        account_base.html
        base.html
        dashboard_base.html
    core/
        index.html
        contact.html
        faq.html
        plans.html
        about.html
    accounts/
        login.html
        register.html
        verify_email.html
        verify_email_success.html
        forgot_password.html
        reset_password.html
    dashboard/
        index.html
```