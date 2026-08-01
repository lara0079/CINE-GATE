# Accessibility checklist

## Implemented

- skip link to main content
- semantic labels and fieldsets
- ARIA tablist, tab, and tabpanel relationships
- left/right/home/end keyboard tab navigation
- visible focus indicators
- result panel focus after review completion
- assertive live announcements for errors and completed actions
- expandable findings using native `details` and `summary`
- descriptive button and export-link text
- reduced-motion support
- responsive tables with horizontal scrolling
- no color-only outcome label: every state is also written as text

## Account-stage verification

- run Lighthouse accessibility audit on the hosted application
- test keyboard-only completion of a review and corrected revision
- test with Android TalkBack or a desktop screen reader
- verify contrast after any final branding changes
- add captions or subtitles to the demonstration video
