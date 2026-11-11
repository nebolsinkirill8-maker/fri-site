# Design
## Source of truth
Active, 2026-11-11. User instructions in this conversation override historical plans. Evidence: site/index.html, site/style.css, CURRENT-STATE.md, PROJECT-CONTEXT.md. Registration side copy rejected by owner: replace with existing FRI botanical/stone artwork, center the readable form. Four organizers, including Kirill with supplied poster.
## Brand
FRI tournament poster: burgundy, raspberry, light paper, stone figure and organizer portraits. Preserve existing identity; no unrelated redesign.
## Product goals
Choose a competition, discover tournament information, watch Twitch, register and sign in. No points economy or predictions until rules are approved.
## Personas and jobs
Visitors choose a tournament and watch; participants manage their account; staff edit content and teams in Django Admin.
## Information architecture
/ selection; /tournament/ team tournament; /zxc/ placeholder; /accounts/ login, registration, profile; /admin/ staff CRM.
## Design principles
Reuse existing poster and typography. Clearly distinguish implemented features from future plans. Never fabricate prizes, dates or formats.
Visitor-first trial: participation/status before video, confirmed content before account creation, ZXC remains secondary. Keep the existing artwork, typography, palette and organizer portraits. Hide unset prize/sponsor/format sections and unpublished forecasts; keep the Twitch link and a user-opened player. Sound only by explicit action on Django tournament page.
## Visual language
Use existing CSS tokens, Onest font, poster imagery, torn shapes and focus treatments in site/style.css. Keep original tournament animations; separate new page styles in site/app.css.
ZXC has a separate look under `site/zxc.css`: black and bone gothic poster, scarlet spider lilies, stone duelist, restrained typography and an ornamental sigil. No autoplay, flashing, fictional rules or dates. Keep the visual language of the team tournament unchanged.
## Components
Shared header, POST logout form, accessible account forms, competition selection links, empty-state panels, responsive stream and channel fallback.
## Accessibility
Semantic headings and labels, keyboard-visible focus, error messages, password autocomplete and reduced motion. Player never obscured. No autoplay on new pages.
## Responsive behavior
Single-column forms and choice cards on narrow screens. Twitch requires 400x300 minimum: hide embedded player below 480 CSS px and retain direct Twitch link.
## Interaction states
Blank prize, sponsors and format blocks are omitted; schedule uncertainty is stated once. ZXC is labeled in development; forecasts are not shown. Forms retain email and show validation errors; anonymous profile redirects to login.
## Content voice
Russian, short and factual. No invented commitments or financial claims.
## Implementation constraints
Django templates, existing CSS/JS assets; session authentication and CSRF. No JWT, frontend framework or external UI dependencies. Local development only; no deployment in this task.
## Open questions
- Profile update 2026-11-11: two-step account → optional nickname, Telegram, Steam, MMR, position. Private own-profile editor; only staff with permissions access these data. Registration has side panels, stacked on mobile. Participants group grants no CRM rights; staff group grants tournament editing, not privilege management. is_staff is separately assigned by a superuser.
- [ ] Owner: tournament board, prize, group/playoff/main-event format and dates remain unset.
- [ ] Owner: ZXC materials expected later.
- [ ] Owner: points and prediction rules deferred; no balance or settlement implementation.
- [ ] Production: HTTPS, mail verification/recovery and login throttling before public release.
