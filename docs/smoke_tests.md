# PrivateCore Smoke Tests v1.1

## 1. Introduction
This document outlines the manual smoke tests for PrivateCore iOS.

## 2. Setup
### 2.1 Photo Injection
Inject at least 2 photos with real GPS EXIF data (Zurich coords: 47.3769Â° N, 8.5417Â° E) so geocoding tests have valid data.

## 3. Test Cases

### PC-T29 [P1][Human]: Geocoding city display
**Goal**: Confirm city + country shown instead of raw lat/lon.
1. Open a GPS-tagged photo detail view.
2. Confirm city + country shown (e.g. "Zurich, Switzerland").

### PC-T30 [P1][Human]: Similar photos carousel
**Goal**: Verify CLIP-based similarity search.
1. Open any photo with clip_embedding_status=done.
2. Confirm horizontal "Similar photos" scroll row appears with \u22651 result.
3. Tap thumbnail navigates to that photo.

### PC-T31 [P1][Human]: WikiDayView navigation
**Goal**: Verify day wiki navigation and content.
1. Open wiki homepage.
2. Tap a blue day link (e.g. "Monday 27 Apr 2026").
3. Confirm WikiDayView loads with photos ribbon, OCR texts, AI descriptions, calendar events for that day.
4. Rescan and Generate buttons visible.

### PC-T32 [P1][Human]: VLM hashtag extraction
**Goal**: Verify AI-generated hashtags.
1. Tap "Describe with AI" on a photo.
2. Confirm 3\u20136 hashtags appear in the tag strip below the description.
3. Tags are lowercase, no # symbol.

### PC-T33 [P1][Human]: iOS People linking
**Goal**: Verify iOS Photos People integration.
1. Open a Person page.
2. Tap toolbar \u2192 "Link iOS Photos People".
3. Picker appears, select a face group.
4. Confirm photos appear in person photo carousel.

### PC-T34 [P2][Human]: Settings Advanced section
**Goal**: Verify advanced settings concealment.
1. Go to Settings.
2. Confirm "Visual index (CLIP)" and "Text embeddings" rows are hidden under collapsed Advanced DisclosureGroup.
3. Main list shows Photos indexed / OCR / AI described / Contacts / Calendar / Database size.