# InLibrary website

The public website for the InLibrary Android app: a product landing page, plus the privacy
policy, terms and conditions, and account deletion page that Google Play needs.

It is plain HTML and CSS: no build step, no dependencies, no JavaScript and no third-party
requests (fonts and images are self-hosted). Edit a file, push it, and the host serves it as-is.
Nothing here depends on the app's code.

| File | What it is |
|---|---|
| `index.html` | Landing page: hero, features, screenshots, privacy summary, policies, contact |
| `privacy.html` | Privacy Policy (includes the India DPDP Act section and grievance officer) |
| `terms.html` | Terms and Conditions (Indian law, users 13+) |
| `delete-account.html` | How to delete an account and data, in the app or by email |
| `404.html` | "Page not found" |
| `style.css` | All styling, with light and dark mode. Brand colours are in `:root` at the top. |
| `fonts/` | Plus Jakarta Sans, the app's font (SIL Open Font License, see `fonts/OFL.txt`) |
| `images/` | App screenshots (`1-timer.webp` … `6-notes.webp`), favicon and touch icon |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |

## Common edits

**Turn on the Google Play button after launch.** In `index.html`, replace the
`<span class="store-pill">…</span>` block with a link using the same class:

```html
<a class="store-pill" href="https://play.google.com/store/apps/details?id=com.dhruv.inlibrary">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3.5v17l14-8.5z" fill="#FF6A00"/></svg>
  <span><small>Get it on</small><strong>Google Play</strong></span>
</a>
```

**Replace screenshots.** Export new 1080×1920 PNGs, convert them to 540px-wide WebP, and keep
the same file names (or update the `<img>` tags and their `alt` text in `index.html`):

```bash
npx --yes sharp-cli -i 1-timer.png -o images/1-timer.webp -f webp -q 80 resize 540
```

**Change features or marketing copy.** Edit the feature cards in `index.html`. Keep claims in
line with `privacy.html`; for example, don't promise "nothing leaves your phone", because library
features share a weekly total.

## Values to keep up to date

There is no template system, so these values are written directly into the pages. To change one,
use find-and-replace across all `*.html` files.

| Value | Current text | Appears in |
|---|---|---|
| Publisher name | `Dhruv Kumar` | all pages |
| Contact / grievance email | `yehdhruvkr@gmail.com` | all pages |
| Policy date | `2 October 2026` | `privacy.html`, `terms.html`, `delete-account.html` |
| Copyright year | `© 2026` | page footers |
| Android package | `com.dhruv.inlibrary` | `privacy.html` |
| Liability cap | `₹1,000` | `terms.html` |

## Updating a policy

1. Edit the text in `privacy.html` or `terms.html`.
2. Change its "Last updated" (and "Effective") date to today.
3. If the app starts collecting new data (for example analytics, crash reporting, payments or a new
   permission), update `privacy.html` **and** the Data safety form in Play Console. They must match.
4. Commit and push. The host redeploys automatically.

Each policy section's `<h2>` has an `id`, and the "On this page" list links to those ids. If
you add or rename a section, update that list too.

The header and footer are repeated in every page. If you add a page, copy an existing one and add
links to it in the other pages' `<nav>` and footer.

## Preview locally

Open `index.html` in a browser, or run a local server:

```bash
npx serve .
```

## Deploy (free)

### GitHub Pages (recommended)

1. Create an empty **public** repository on GitHub named `inlibrary-site` (free GitHub Pages
   needs a public repo). Don't add a README.
2. Push this folder:
   ```bash
   git remote add origin https://github.com/<your-username>/inlibrary-site.git
   git push -u origin main
   ```
3. On GitHub, go to **Settings → Pages**. Under "Build and deployment", choose **Deploy from a branch**,
   then branch **main** and folder **/ (root)**, and save.
4. After about a minute the site is live at `https://<your-username>.github.io/inlibrary-site/`.

### Cloudflare Pages

Go to Workers & Pages → Create → Pages → Connect to Git, then pick the repo. Leave the build
command empty and set the output directory to `/`. The URL will look like
`https://inlibrary-site.pages.dev/`.

### Netlify

Go to Add new site → Import an existing project, then pick the repo. Leave the build command
empty and set the publish directory to `.`. You can also drag this folder onto
app.netlify.com/drop. The URL will look like `https://<name>.netlify.app/`.

All links are relative, so the site works at a domain root or under a subpath.

## Where the URLs go in Play Console

Replace `<site>` with your live URL, for example `https://<your-username>.github.io/inlibrary-site`.

| Play Console field | URL |
|---|---|
| App content → Privacy policy | `<site>/privacy.html` |
| App content → Data safety → Delete account URL | `<site>/delete-account.html` |
| Store listing → Website (optional) | `<site>/` |

Google checks that the policy names the same developer as your Play listing. If your Play
Console developer name is not `Dhruv Kumar`, change the publisher name in the pages to match it.

Terms (`<site>/terms.html`) are not a Play Console field. Link them from the app or the store
description if you want.

## Data safety form, as described by this policy

Use this as a starting point when you fill in the Play Console form. Check it against the
current app before you submit.

- **Data collected (only when the user signs in or uses the Library tab):** Personal info: name,
  email address, user IDs. App activity: other user-generated content (library display name and
  name, weekly study total).
- **Shared with third parties:** No. Supabase and Google act as service providers, which Play
  does not count as sharing.
- **Encrypted in transit:** Yes.
- **Users can request deletion:** Yes (in the app and by email).
- **Optional:** Yes. All online data comes from optional features.
- Data kept only on the device (sessions, notes, photos) does not count as "collected".
