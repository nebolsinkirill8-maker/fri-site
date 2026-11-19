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
Account design: login uses poster-edge art with a compact dark form. Profile is a two-column player pass and application dashboard, collapsing to one column on mobile. All seven profile fields stay in the pass; statuses retain backend values and applications remain separate. Existing poster assets are reused, with no fake player avatars, rankings or participation claims.
Profile editor: grouped dark fields (game data / contacts / equipment), a paper reference panel with an SVG print mark rather than repeated statue art. Microphone/webcam are optional self-reported yes/no/unspecified; no device access. Existing eligibility and application requirements do not change.
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

## Visitor gateway update, 2026-11-12
Home is a two-poster competition gateway with direct tournament/ZXC navigation, never a registration gate. Participation instructions sit after organizers and before sponsors. Receding sponsor cards dim continuously to 45% brightness; reduced motion restores full brightness. Sponsor dots fade vertically and paper overlaps the FAQ edge by 3px to avoid a compositing hairline. Existing account flow and organizer carousel remain unchanged.

Profile update: team names are staff-owned and absent from the participant editor. Both equipment questions require an explicit yes/no answer when saving; neither device is required. Existing unspecified data remain unchanged until the next save.

Dashboard UI/UX pass: preserve FRI palette and Onest typography instead of adopting the search engine's generic gaming font/WebGL recommendation. Apply the verified heading-hierarchy and status-feedback guidance: explicit decision explanations, readable 14–15px supporting text, 44px actions, consistent focus rings and reduced-motion handling. Keep DOM and mobile visual order aligned; no application rules or personal data changes.

Dashboard correction: omit in-page shortcut navigation when all destinations are directly visible below the heading; retain edit-profile and contextual support actions.

21st integration, 2026-11-12: Verified local ui-ux-pro-max skill and authenticated MCP 21st search/retrieval. Retrieved Status Badge demo 521 by serafimcloud (https://21st.dev/@serafimcloud/components/status-badge). Adapted its split status/reference layout and decorative state icon into partials/application_badge.html and profile.css; no React, CVA or icon dependency added. Existing backend statuses and routes drive every badge/action. Search recommendations remain advisory; FRI brand tokens override generic gaming palettes. No redundant section navigation. Browser QA uses a disposable account, never real participant credentials.

## Full participant-route UI audit, 2026-11-12
Reviewed home, team tournament, ZXC, login, registration, profile, editor, both application routes, support inbox and thread. Existing branded marketing/account pages retained. Redesigned application flows with a responsive decision surface and paper help panel; registration gets matching dark form controls, clear errors and a full-width CTA. Support is now a dedicated compose/inbox view with conversation bubbles, staff paper replies and a closed-thread panel. Admin remains Django's protected staff interface, not a participant marketing page.
21st: retrieved Empty State by wensity, demo 27575, https://21st.dev/@wensity/components/empty-state; adapted centered illustration/title/description pattern to closed intake and support empty list. Prior demo 521 status badge reused. No framework/dependency installation. Skill guidance: visible field errors plus linked focusable error summary; existing brand overrides generic recommendations.
Browser audit at 375/1440 CSS px: participant routes have no horizontal overflow or broken loaded images. Login, opening application/editor, support reply persistence verified using a disposable QA account. Actual intake gates and participant records were not changed.

Home redesign, 2026-11-12: replaced boxed dark cards with a full editorial diptych: warm paper/oversized FRI/stone figure for team play, black scarlet botanical duel poster for ZXC. A short masthead introduces the choice; each entire poster is a semantic direct link. No registration gate. 21st split-hero metadata demo19078 reviewed as a layout reference only (no source retrieval claimed; daily quota exhausted in prior task); implementation is native Django/CSS with existing FRI artwork. ui-ux-pro-max design-system search informed hierarchy but brand typography/palette preserved instead of generic neon/WebGL. Phone stacks posters, desktop shows the diptych; reduced motion disables transforms.
