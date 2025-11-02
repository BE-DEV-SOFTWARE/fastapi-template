# Email Configuration

This template uses an email forwarding service called [Brevo](https://www.brevo.com/) (formerly Sendinblue) to send transactional emails like verification codes, password resets, and welcome messages. Instead of connecting directly to an SMTP server, we use Brevo's API which handles all the complexity of email delivery for us.

## Why Use an Email Forwarding Service?

You might be wondering why use a service like Brevo instead of just connecting directly to Gmail or your own SMTP server. The short answer is: it makes your life easier and your emails deliverability more reliable!

When you send emails through a service like Brevo, they take care of all the technical stuff that ensures your emails actually reach people's inboxes. Things like making sure your emails don't end up in spam folders, handling bounces when someone's email address doesn't work anymore, and managing the reputation of your sending domain. They also handle the infrastructure so you don't have to worry about rate limits, server capacity, or email authentication protocols like SPF and DKIM. 

>[!NOTE]
SPF, DKIM and DMARC are still managed at domain level but Brevo will help your verify if your DNS is set up properly.

This means you can focus on building your app instead of wrestling with email server configurations. Plus, Brevo offers a free plan with 300 emails per day, which is perfect for development and small projects. If you need to switch to another service like MailerSend or SendGrid later, you can easily modify the code in `app/email_service/base.py` to use their API instead.

>[!TIP]
I personally tested all of them and Brevo propose the best Free plan out there + it supports multiple domains

## Setting Up Brevo

Getting started with Brevo is pretty straightforward. First, head over to [brevo.com](https://www.brevo.com/) and sign up for a free account. Once you're in, you'll need to get your API key. Navigate to the "SMTP & API" section in your dashboard, then go to "API Keys" and create a new one (or use an existing one if you have it).

For production use, you'll also want to verify your domain in Brevo. This helps ensure your emails are properly authenticated and less likely to be marked as spam. Brevo will guide you through adding some DNS records to your domain.

Once you have your API key, add it to your `.env` file along with your email settings:

```bash
EMAILS_FROM_EMAIL=your-email@yourdomain.com
EMAILS_FROM_NAME=Your Project Name
BREVO_API_KEY=your-brevo-api-key-here
```

That's it! Your backend is now configured to send emails through Brevo, and you're all set to scale up!

## Email Templates with MJML

One of the nice things about this template is that it gives you full control over how your emails look. Instead of being stuck with branded templates from your email forwarding service, you can design your emails exactly how you want them using [MJML](https://mjml.io/).

>[!TIP]
To edit your emails quickly use an [existing MJML template](https://mjml.io/templates) and customize it using the [MJML official live editor](https://mjml.io/try-it-live)

MJML is a markup language designed specifically for emails. The problem with regular HTML in emails is that different email clients (Gmail, Outlook, Apple Mail, etc.) all handle HTML differently, which makes creating responsive email designs a nightmare. MJML solves this by letting you write simple, clean code that automatically gets converted into HTML that works across all email clients.

You'll find the email templates for this project in `app/email_service/templates/src/` as `.mjml` files. There are templates for new account welcome emails, password resets, verification codes, and a simple test email. 

>[!TIP]
If you code in VSCode (or Cursor) you can preview and build your template using this extension: [MJML by Attila Buti](https://marketplace.visualstudio.com/items?itemName=attilabuti.vscode-mjml)

>[!CAUTION]
Don't forget to compile your MJML template in HTML and put it in the `templates/build` folder. With the VSCode extension you can hit CTRL+Shift+P (or CMD+Shift+P on mac) and run 'MJML: Export HTML'


Each template uses Jinja2 for dynamic content, so you can insert things like the user's email address, verification codes, or links. Common variables available in all templates include `{{ project_name }}`, `{{ signature }}`, `{{ web_app_url }}`, and `{{ email }}`. If you want to customize how your emails look, just edit the `.mjml` files - the templates will be rebuilt the next time you build your Docker containers.

## Enabling and Disabling Email Service

By default, the email service is enabled (`ENABLE_EMAIL_SERVICE=True`).

If you want to disable the email service entirely (maybe you're running tests or don't need emails for a particular deployment), just set `ENABLE_EMAIL_SERVICE=False` in your `.env` file. When disabled, the backend will log a message instead of attempting to send emails, and your code won't break if email credentials aren't configured.

For the email service to actually send emails, you need both `ENABLE_EMAIL_SERVICE=True` (which is the default) and proper email configuration. The backend automatically enables email sending (`EMAILS_ENABLED=True`) when you provide both a `BREVO_API_KEY` and `EMAILS_FROM_EMAIL`. So in production, just make sure you've set those values in your `.env` file and you're good to go!
